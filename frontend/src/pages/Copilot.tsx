import { useState } from 'react'
import { copilotChat } from '@/api/copilot'
import { useFields } from '@/api/fields'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

export function Copilot() {
  const [fieldId, setFieldId] = useState('')
  const [message, setMessage] = useState('Should I irrigate this field today?')
  const [answer, setAnswer] = useState<string | null>(null)
  const [mode, setMode] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { data: fields } = useFields()

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!fieldId.trim()) {
      setError('Select a field.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await copilotChat(fieldId, message)
      setAnswer(res.answer)
      setMode(res.mode)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed')
      setAnswer(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Farm Copilot</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="field">Field</Label>
              <select
                id="field"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={fieldId}
                onChange={(e) => setFieldId(e.target.value)}
              >
                <option value="">Select field…</option>
                {fields?.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="message">Question</Label>
              <Textarea
                id="message"
                rows={4}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" disabled={loading}>
              {loading ? 'Thinking…' : 'Ask Copilot'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {answer && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Response {mode ? <span className="text-muted-foreground">({mode})</span> : null}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap text-sm">{answer}</pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
