from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from auth import require_manager
from db import get_orders_collection, get_stock_collection
from models import OrderCreate, OrderResponse, OrderUpdate
from services.email import send_confirmation_email

router = APIRouter()


def order_doc_to_response(doc: dict) -> OrderResponse:
    return OrderResponse(
        id=str(doc["_id"]),
        email=doc["email"],
        phone=doc["phone"],
        venmo_username=doc["venmo_username"],
        affiliation=doc["affiliation"],
        cart_item=doc["cart_item"],
        total=doc["total"],
        status=doc["status"],
        created_at=doc["created_at"],
    )


@router.post("/", response_model=OrderResponse, status_code=201)
async def create_order(order: OrderCreate):
    order_dict = order.model_dump()
    order_dict["total"] = order.cart_item.price * order.cart_item.quantity
    order_dict["status"] = "pending"
    order_dict["created_at"] = datetime.now(timezone.utc)

    stock = get_stock_collection()
    stock_doc = await stock.find_one({"size": order.cart_item.size.value})
    if not stock_doc or stock_doc["count"] < order.cart_item.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock for this size")

    await stock.update_one(
        {"size": order.cart_item.size.value},
        {"$inc": {"count": -order.cart_item.quantity}},
    )

    collection = get_orders_collection()
    result = await collection.insert_one(order_dict)

    await send_confirmation_email(
        to_email=order.email,
        order_id=str(result.inserted_id),
        cart_item=order.cart_item,
        total=order_dict["total"],
    )

    order_dict["_id"] = result.inserted_id
    return order_doc_to_response(order_dict)


@router.get(
    "/",
    response_model=list[OrderResponse],
    dependencies=[Depends(require_manager)],
)
async def list_orders():
    collection = get_orders_collection()
    orders = []
    async for doc in collection.find().sort("created_at", -1):
        orders.append(order_doc_to_response(doc))
    return orders


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    dependencies=[Depends(require_manager)],
)
async def get_order(order_id: str):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order ID")

    collection = get_orders_collection()
    doc = await collection.find_one({"_id": ObjectId(order_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")

    return order_doc_to_response(doc)


@router.patch(
    "/{order_id}",
    response_model=OrderResponse,
    dependencies=[Depends(require_manager)],
)
async def update_order(order_id: str, update: OrderUpdate):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order ID")

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    collection = get_orders_collection()
    result = await collection.find_one_and_update(
        {"_id": ObjectId(order_id)},
        {"$set": update_data},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Order not found")

    return order_doc_to_response(result)


@router.delete(
    "/{order_id}",
    status_code=204,
    dependencies=[Depends(require_manager)],
)
async def delete_order(order_id: str):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order ID")

    collection = get_orders_collection()
    result = await collection.delete_one({"_id": ObjectId(order_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
