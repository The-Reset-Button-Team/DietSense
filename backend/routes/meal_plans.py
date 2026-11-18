"""
DietSense — Meal Plans Routes
Allows authenticated users to generate, persist, and retrieve daily/weekly meal plans.
Data is persisted to local SQLite database with strict user ownership enforcement.
Mutations are enqueued into the local sync_queue for cloud synchronization.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response, PlainTextResponse
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import json
import uuid

from app.core.dependencies import get_current_user
from db.database import get_db_cursor
from app.core.sync_service import enqueue_sync_operation

router = APIRouter(tags=["Meal Plans"])

VALID_PLAN_STATUSES = {"generated", "accepted", "completed"}


def _row_to_plan(row: Any) -> Dict[str, Any]:
    """Converts a SQLite meal_plan row to dictionary."""
    items = []
    if row["items"]:
        try:
            items = json.loads(row["items"])
        except Exception:
            items = []
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "date": row["date"],
        "target_calories": int(row["target_calories"]),
        "items": items,
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"] if "updated_at" in row.keys() and row["updated_at"] else row["created_at"],
    }


@router.get("/meal-plans")
@router.get("/meal_plans")
async def get_meal_plans(
    date: Optional[str] = Query(None, description="Filter plans by exact date (YYYY-MM-DD)"),
    start_date: Optional[str] = Query(None, description="Start date for range filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date for range filter (YYYY-MM-DD)"),
    plan_status: Optional[str] = Query(None, alias="status", description="Filter by status (generated, accepted, completed)"),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve meal plans created by the authenticated user with optional date and status filters.
    Enforces strict user data isolation.
    """
    user_id = user["id"]
    query = "SELECT * FROM meal_plans WHERE user_id = ?"
    params: List[Any] = [user_id]

    if date:
        query += " AND date = ?"
        params.append(date)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if plan_status:
        query += " AND status = ?"
        params.append(plan_status)

    query += " ORDER BY date DESC, created_at DESC"

    with get_db_cursor() as cur:
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        return [_row_to_plan(r) for r in rows]


@router.get("/meal-plans/weekly")
@router.get("/meal_plans/weekly")
async def get_weekly_meal_plans(
    start_date: Optional[str] = Query(None, description="Start date of the week (YYYY-MM-DD)"),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve meal plans for a 7-day week starting from start_date (or current Monday).
    Returns an array of 7 day slots with either the plan or null if not planned yet.
    """
    user_id = user["id"]

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format, expected YYYY-MM-DD")
    else:
        now = datetime.now(timezone.utc)
        # Default to Monday of current week
        start_dt = now - timedelta(days=now.weekday())

    dates = [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    end_date_str = dates[-1]
    start_date_str = dates[0]

    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT * FROM meal_plans
            WHERE user_id = ? AND date >= ? AND date <= ?
            ORDER BY date ASC, created_at DESC
            """,
            (user_id, start_date_str, end_date_str),
        )
        rows = cur.fetchall()

    plans_by_date: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        d = r["date"]
        if d not in plans_by_date:  # Keep newest per date
            plans_by_date[d] = _row_to_plan(r)

    weekly_schedule = []
    for d in dates:
        weekly_schedule.append({
            "date": d,
            "plan": plans_by_date.get(d, None),
        })

    return {
        "start_date": start_date_str,
        "end_date": end_date_str,
        "days": weekly_schedule,
    }


@router.post("/meal-plans", status_code=status.HTTP_201_CREATED)
@router.post("/meal_plans", status_code=status.HTTP_201_CREATED)
async def create_meal_plan(
    plan_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Create and persist a new meal plan composed of recommended recipes/meals.
    Guarantees user ownership (user_id derived exclusively from JWT).
    Enqueues mutation to local sync_queue.
    """
    user_id = user["id"]
    custom_id = plan_data.get("id") or plan_data.get("plan_id")
    plan_id = custom_id if custom_id else f"plan_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    created_at = now.isoformat()
    plan_date = plan_data.get("date", now.strftime("%Y-%m-%d"))
    target_cal = int(plan_data.get("target_calories", 2000))
    items_json = json.dumps(plan_data.get("items", []))
    plan_status = plan_data.get("status", "generated")

    if plan_status not in VALID_PLAN_STATUSES:
        plan_status = "generated"

    with get_db_cursor() as cur:
        # Check if updating an existing plan by ID
        cur.execute("SELECT * FROM meal_plans WHERE id = ? AND user_id = ?", (plan_id, user_id))
        existing = cur.fetchone()

        if existing:
            cur.execute(
                """
                UPDATE meal_plans
                SET date = ?, target_calories = ?, items = ?, status = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
                """,
                (plan_date, target_cal, items_json, plan_status, created_at, plan_id, user_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO meal_plans (id, user_id, date, target_calories, items, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (plan_id, user_id, plan_date, target_cal, items_json, plan_status, created_at, created_at),
            )

        cur.execute("SELECT * FROM meal_plans WHERE id = ?", (plan_id,))
        row = cur.fetchone()

    # Enqueue mutation for cloud synchronization
    enqueue_sync_operation(
        user_id=user_id,
        entity_type="meal_plan",
        entity_id=plan_id,
        operation="UPSERT",
        payload={
            "id": plan_id,
            "user_id": user_id,
            "date": plan_date,
            "target_calories": target_cal,
            "items": plan_data.get("items", []),
            "status": plan_status,
            "created_at": created_at,
            "updated_at": created_at,
        },
    )

    return _row_to_plan(row)


@router.get("/meal-plans/{plan_id}")
@router.get("/meal_plans/{plan_id}")
async def get_meal_plan_by_id(
    plan_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve a specific meal plan by ID, verifying user ownership.
    Prevents cross-user data leakage.
    """
    user_id = user["id"]
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT * FROM meal_plans WHERE id = ? AND user_id = ?",
            (plan_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Meal plan not found or access denied")
        return _row_to_plan(row)


@router.patch("/meal-plans/{plan_id}/status")
@router.patch("/meal_plans/{plan_id}/status")
@router.put("/meal-plans/{plan_id}/status")
@router.put("/meal_plans/{plan_id}/status")
async def update_meal_plan_status(
    plan_id: str,
    status_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Update the status of an existing meal plan (e.g. generated -> accepted -> completed).
    Verifies strict user ownership before mutation.
    """
    user_id = user["id"]
    new_status = status_data.get("status")

    if not new_status or new_status not in VALID_PLAN_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{new_status}'. Allowed values: {sorted(list(VALID_PLAN_STATUSES))}",
        )

    now = datetime.now(timezone.utc).isoformat()

    with get_db_cursor() as cur:
        cur.execute(
            "SELECT * FROM meal_plans WHERE id = ? AND user_id = ?",
            (plan_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Meal plan not found or access denied")

        cur.execute(
            "UPDATE meal_plans SET status = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (new_status, now, plan_id, user_id),
        )
        cur.execute("SELECT * FROM meal_plans WHERE id = ?", (plan_id,))
        updated_row = cur.fetchone()

    enqueue_sync_operation(
        user_id=user_id,
        entity_type="meal_plan",
        entity_id=plan_id,
        operation="UPSERT",
        payload=_row_to_plan(updated_row),
    )

    return _row_to_plan(updated_row)


@router.delete("/meal-plans/{plan_id}")
@router.delete("/meal_plans/{plan_id}")
async def delete_meal_plan(
    plan_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Delete a meal plan belonging to the authenticated user.
    Enforces user data isolation.
    """
    user_id = user["id"]
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT * FROM meal_plans WHERE id = ? AND user_id = ?",
            (plan_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Meal plan not found or access denied")

        cur.execute("DELETE FROM meal_plans WHERE id = ? AND user_id = ?", (plan_id, user_id))

    enqueue_sync_operation(
        user_id=user_id,
        entity_type="meal_plan",
        entity_id=plan_id,
        operation="DELETE",
        payload={"id": plan_id},
    )

    return {"status": "success", "message": f"Meal plan {plan_id} deleted"}


# ─── Phase 8F: Export Endpoints ──────────────────────────────────────────────

def _resolve_plan(plan_id: str, user_id: str, cur) -> Dict[str, Any]:
    """Resolves plan_id ('today', 'current', or actual ID) to a plan dict."""
    if plan_id in ("today", "current"):
        cur.execute(
            "SELECT * FROM meal_plans WHERE user_id = ? ORDER BY date DESC, created_at DESC LIMIT 1",
            (user_id,),
        )
    else:
        cur.execute(
            "SELECT * FROM meal_plans WHERE id = ? AND user_id = ?",
            (plan_id, user_id),
        )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Meal plan not found or access denied")
    return _row_to_plan(row)


@router.get("/meal-plans/{plan_id}/export/text", response_class=PlainTextResponse)
@router.get("/meal_plans/{plan_id}/export/text", response_class=PlainTextResponse)
async def export_meal_plan_text(
    plan_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Export a meal plan as a formatted plain-text summary."""
    user_id = user["id"]
    with get_db_cursor() as cur:
        plan = _resolve_plan(plan_id, user_id, cur)

    items: List[Dict[str, Any]] = plan.get("items", [])
    date_str = plan.get("date", "N/A")
    plan_status = plan.get("status", "generated")

    lines = [
        "=" * 50,
        "   DietSense Meal Plan",
        f"   Date   : {date_str}",
        f"   Status : {plan_status}",
        "=" * 50,
        "",
    ]

    total_cal = 0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0

    for item in items:
        slot = item.get("slotName") or item.get("slot_name") or item.get("key", "Meal")
        name = item.get("name", "Unknown Meal")
        cal = item.get("calories", 0) or 0
        protein = item.get("protein_g", 0.0) or 0.0
        carbs = item.get("carbs_g", 0.0) or 0.0
        fat = item.get("fat_g", 0.0) or 0.0

        total_cal += cal
        total_protein += protein
        total_carbs += carbs
        total_fat += fat

        lines.append(f"[{slot}]")
        lines.append(f"  Meal    : {name}")
        lines.append(f"  Calories: {cal} kcal")
        lines.append(f"  Protein : {protein:.1f}g")
        lines.append(f"  Carbs   : {carbs:.1f}g")
        lines.append(f"  Fat     : {fat:.1f}g")
        lines.append("")

    lines += [
        "-" * 50,
        "TOTALS",
        f"  Calories: {total_cal} kcal",
        f"  Protein : {total_protein:.1f}g",
        f"  Carbs   : {total_carbs:.1f}g",
        f"  Fat     : {total_fat:.1f}g",
        "=" * 50,
    ]

    return "\n".join(lines)


@router.get("/meal-plans/{plan_id}/export/whatsapp", response_class=PlainTextResponse)
@router.get("/meal_plans/{plan_id}/export/whatsapp", response_class=PlainTextResponse)
async def export_meal_plan_whatsapp(
    plan_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Export a meal plan as WhatsApp-flavored markdown text."""
    user_id = user["id"]
    with get_db_cursor() as cur:
        plan = _resolve_plan(plan_id, user_id, cur)

    items: List[Dict[str, Any]] = plan.get("items", [])
    date_str = plan.get("date", "N/A")

    # Slot → emoji mapping (by common slot names)
    SLOT_EMOJIS = {
        "early morning": "☀️",
        "breakfast": "🥣",
        "lunch": "🍱",
        "snack": "🍎",
        "dinner": "🌙",
        "mid morning": "🍎",
        "pre-workout": "💪",
        "post-workout": "🥤",
    }

    lines = [
        f"*DietSense Meal Plan — {date_str}*",
        "",
    ]

    total_cal = 0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0

    for item in items:
        slot = item.get("slotName") or item.get("slot_name") or item.get("key", "Meal")
        name = item.get("name", "Unknown Meal")
        cal = item.get("calories", 0) or 0
        protein = item.get("protein_g", 0.0) or 0.0
        carbs = item.get("carbs_g", 0.0) or 0.0
        fat = item.get("fat_g", 0.0) or 0.0

        total_cal += cal
        total_protein += protein
        total_carbs += carbs
        total_fat += fat

        emoji = SLOT_EMOJIS.get(slot.lower(), "🍽️")
        lines.append(f"{emoji} *{slot}*")
        lines.append(f"• {name} — {cal} kcal")
        lines.append(f"_P:{protein:.0f}g | C:{carbs:.0f}g | F:{fat:.0f}g_")
        lines.append("")

    lines.append(f"*Total: {total_cal} kcal*")
    lines.append(f"_P:{total_protein:.0f}g | C:{total_carbs:.0f}g | F:{total_fat:.0f}g_")
    lines.append("")
    lines.append("_Sent via DietSense 🥗_")

    return "\n".join(lines)


@router.get("/meal-plans/{plan_id}/export/pdf")
@router.get("/meal_plans/{plan_id}/export/pdf")
async def export_meal_plan_pdf(
    plan_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Export a meal plan as a raw PDF binary (pure Python, no reportlab)."""
    user_id = user["id"]
    with get_db_cursor() as cur:
        plan = _resolve_plan(plan_id, user_id, cur)

    items: List[Dict[str, Any]] = plan.get("items", [])
    date_str = plan.get("date", "N/A")

    # Build text lines for the PDF stream
    total_cal = 0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0

    text_lines = [
        "DietSense Meal Plan",
        f"Date: {date_str}",
        f"Status: {plan.get('status', 'generated')}",
        "",
    ]

    for item in items:
        slot = item.get("slotName") or item.get("slot_name") or item.get("key", "Meal")
        name = item.get("name", "Unknown Meal")
        cal = item.get("calories", 0) or 0
        protein = item.get("protein_g", 0.0) or 0.0
        carbs = item.get("carbs_g", 0.0) or 0.0
        fat = item.get("fat_g", 0.0) or 0.0

        total_cal += cal
        total_protein += protein
        total_carbs += carbs
        total_fat += fat

        text_lines.append(f"[{slot}] {name}")
        text_lines.append(f"  {cal} kcal | P:{protein:.0f}g C:{carbs:.0f}g F:{fat:.0f}g")

    text_lines += [
        "",
        "--- TOTALS ---",
        f"Total Calories: {total_cal} kcal",
        f"Protein: {total_protein:.1f}g | Carbs: {total_carbs:.1f}g | Fat: {total_fat:.1f}g",
    ]

    # Build raw PDF using the same approach as create_mock_receipt_pdf
    text_commands = []
    y = 740
    for line in text_lines:
        clean = line.replace("(", "\\(").replace(")", "\\)")
        text_commands.append(f"1 0 0 1 50 {y} Tm ({clean}) Tj")
        y -= 20
        if y < 50:
            break  # Safety: don't overflow page

    stream_content = "BT\n/F1 12 Tf\n" + "\n".join(text_commands) + "\nET"
    stream_bytes = stream_content.encode("latin-1")
    length = len(stream_bytes)

    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj <</Length " + str(length).encode("latin-1") + b">> stream\n"
        + stream_bytes
        + b"\nendstream\nendobj\n"
        b"5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"trailer <</Size 6 /Root 1 0 R>>\nstartxref\n999\n%%EOF"
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"dietsense_meal_plan_{date_str}.pdf\""},
    )


# ─── Phase 8F: Cook Mode ──────────────────────────────────────────────────────

@router.get("/meal-plans/recipes/{recipe_id}/cook")
@router.get("/meal_plans/recipes/{recipe_id}/cook")
async def get_cook_mode_recipe(
    recipe_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Cook Mode — Returns a structured step-by-step cooking guide for a recipe.
    Looks up the recipe in CANONICAL_RECIPES from pantry routes; falls back to defaults.
    """
    from backend.routes.pantry import CANONICAL_RECIPES

    recipe = next((r for r in CANONICAL_RECIPES if r["id"] == recipe_id), None)

    if recipe:
        name = recipe["name"]
        ingredients_raw = recipe.get("required_ingredients", [])
        instructions_raw = recipe.get("instructions", "")

        # Build ingredient list
        ingredients = [
            {"name": ing, "quantity": "as needed", "is_prepped": False}
            for ing in ingredients_raw
        ]

        # Split instructions into steps (split on '. ' or ',' for simple parsing)
        raw_steps = [s.strip() for s in instructions_raw.replace(". ", ".|").replace(", ", ",").split("|") if s.strip()]
        if not raw_steps:
            raw_steps = [instructions_raw] if instructions_raw else ["Prepare and cook as directed."]

        steps = []
        for i, instruction in enumerate(raw_steps, start=1):
            steps.append({
                "step_num": i,
                "instruction": instruction,
                "timer_recommended_seconds": 120 * i,
                "ingredients_needed": ingredients_raw[:2] if i == 1 else ingredients_raw[i - 1:i],
            })

        return {
            "id": recipe["id"],
            "name": name,
            "prep_time_mins": 5,
            "cook_time_mins": 10,
            "total_steps": len(steps),
            "steps": steps,
            "ingredients": ingredients,
        }

    # Fallback for unknown recipe_id
    return {
        "id": recipe_id,
        "name": f"Recipe #{recipe_id}",
        "prep_time_mins": 5,
        "cook_time_mins": 10,
        "total_steps": 3,
        "steps": [
            {
                "step_num": 1,
                "instruction": "Gather and prepare all ingredients.",
                "timer_recommended_seconds": 120,
                "ingredients_needed": ["water", "salt"],
            },
            {
                "step_num": 2,
                "instruction": "Cook over medium heat until done.",
                "timer_recommended_seconds": 300,
                "ingredients_needed": [],
            },
            {
                "step_num": 3,
                "instruction": "Plate and serve immediately.",
                "timer_recommended_seconds": 60,
                "ingredients_needed": [],
            },
        ],
        "ingredients": [
            {"name": "Water", "quantity": "as needed", "is_prepped": False},
            {"name": "Salt", "quantity": "to taste", "is_prepped": False},
        ],
    }
