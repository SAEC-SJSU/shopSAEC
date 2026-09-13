import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || ''

interface Order {
  id: string
  email: string
  phone: string
  venmo_username: string
  affiliation: string
  cart_item: {
    item: string
    size: string
    quantity: number
    price: number
  }
  total: number
  status: string
  created_at: string
}

export default function ActiveOrders({
  token,
  onSessionExpired,
}: {
  token: string
  onSessionExpired: () => void
}) {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState<string | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchOrders()
  }, [])

  async function fetchOrders() {
    try {
      const res = await fetch(`${API_URL}/api/orders/`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.status === 401) {
        onSessionExpired()
        return
      }
      if (res.ok) {
        const data = await res.json()
        setOrders(data)
      } else {
        setError('Failed to load orders.')
      }
    } catch {
      setError('Failed to load orders.')
    } finally {
      setLoading(false)
    }
  }

  async function markCompleted(orderId: string) {
    setUpdating(orderId)
    setError('')
    try {
      const res = await fetch(`${API_URL}/api/orders/${orderId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ status: 'completed' }),
      })
      if (res.status === 401) {
        onSessionExpired()
        return
      }
      if (res.ok) {
        setOrders((prev) =>
          prev.map((o) =>
            o.id === orderId ? { ...o, status: 'completed' } : o,
          ),
        )
      } else {
        setError('Failed to update order.')
      }
    } catch {
      setError('Failed to update order.')
    } finally {
      setUpdating(null)
    }
  }

  if (loading) {
    return <span className="opacity-60">Loading orders...</span>
  }

  if (error && orders.length === 0) {
    return <span className="text-sm text-red-400">{error}</span>
  }

  if (orders.length === 0) {
    return <span className="opacity-60">No orders found.</span>
  }

  return (
    <div className="flex flex-col gap-4">
      {error && <span className="text-sm text-red-400">{error}</span>}
      {orders.map((order) => (
        <div
          key={order.id}
          className="border-2 border-blue-100/20 rounded-md p-4 sm:p-6"
        >
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div className="flex flex-col gap-1">
              <span className="text-sm font-medium">
                {order.cart_item.item} — {order.cart_item.size} x
                {order.cart_item.quantity}
              </span>
              <span className="text-xs opacity-60">${order.total}.00</span>
            </div>
            <span
              className={`text-xs px-2 py-0.5 rounded-2xl border w-fit ${
                order.status === 'completed'
                  ? 'bg-green-500/20 border-green-400/30 text-green-300'
                  : 'bg-yellow-500/20 border-yellow-400/30 text-yellow-300'
              }`}
            >
              {order.status}
            </span>
          </div>

          <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm opacity-80">
            <div>
              <span className="opacity-60">Email: </span>
              {order.email}
            </div>
            <div>
              <span className="opacity-60">Phone: </span>
              {order.phone}
            </div>
            <div>
              <span className="opacity-60">Venmo: </span>@{order.venmo_username}
            </div>
            <div>
              <span className="opacity-60">Affiliation: </span>
              {order.affiliation}
            </div>
          </div>

          <div className="mt-2 text-xs opacity-40">
            {new Date(order.created_at).toLocaleString()}
          </div>

          {order.status === 'pending' && (
            <button
              onClick={() => markCompleted(order.id)}
              disabled={updating === order.id}
              className={`mt-4 px-6 py-1.5 text-sm rounded-4xl transition-all duration-300 ${
                updating === order.id
                  ? 'bg-neutral-200/10 border border-neutral-50/10 opacity-50 cursor-not-allowed'
                  : 'bg-green-500/20 border border-green-400/30 hover:bg-green-500/30 cursor-pointer'
              }`}
            >
              {updating === order.id ? 'Updating...' : 'Mark Completed'}
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
