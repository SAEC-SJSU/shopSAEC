import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import ActiveOrders from '#/components/Manager/ActiveOrders'

const API_URL = import.meta.env.VITE_API_URL || ''

export const Route = createFileRoute('/manager')({
  component: ManagerPage,
})

function ManagerPage() {
  const [password, setPassword] = useState('')
  // Held in memory only: never persisted, so it dies with the tab.
  const [token, setToken] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const res = await fetch(`${API_URL}/api/manager/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })

      if (res.status === 429) {
        setError('Too many attempts, please wait a few minutes')
        return
      }

      if (!res.ok) {
        throw new Error('Invalid password')
      }

      const data = await res.json()
      if (!data.token) {
        throw new Error('No token returned')
      }

      setToken(data.token)
      // The password has done its job; drop it rather than keep it around.
      setPassword('')
    } catch {
      setError('Invalid password')
    } finally {
      setLoading(false)
    }
  }

  function handleSessionExpired() {
    setToken('')
    setPassword('')
    setError('Session expired, please log in again')
  }

  if (!token) {
    return (
      <div className="mt-2 mx-2 sm:mx-4 flex flex-col justify-center items-center">
        <div className="w-full max-w-md pb-8 rounded-md border-2 border-blue-100/30 bg-blue-950-950/20 p-8">
          <div className="p-4 border-b border-neutral-200/20 mb-6">
            <span className="text-lg">Manager Login</span>
          </div>
          <form onSubmit={handleLogin} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm opacity-70">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter manager password"
                className="px-3 py-2 bg-neutral-200/10 border border-neutral-200/20 rounded-md text-sm focus:outline-none focus:border-blue-400/50"
              />
            </div>
            {error && <span className="text-sm text-red-400">{error}</span>}
            <button
              type="submit"
              disabled={loading || !password}
              className={`px-8 py-2 rounded-4xl transition-all duration-300 ${
                loading || !password
                  ? 'bg-neutral-200/10 border border-neutral-50/10 opacity-50 cursor-not-allowed'
                  : 'bg-neutral-200/20 border border-neutral-50/20 hover:bg-neutral-100/30 cursor-pointer'
              }`}
            >
              {loading ? 'Checking...' : 'Login'}
            </button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="mt-2 mx-2 sm:mx-4 flex flex-col justify-center items-center">
      <div className="w-full max-w-4xl pb-8 rounded-md border-2 border-blue-100/30 bg-blue-950-950/20">
        <div className="p-4 border-b border-neutral-200/20">
          <span className="text-lg">Order Manager</span>
        </div>
        <div className="mx-4 sm:mx-8 mt-6">
          <ActiveOrders token={token} onSessionExpired={handleSessionExpired} />
        </div>
      </div>
    </div>
  )
}
