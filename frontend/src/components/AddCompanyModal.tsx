import { useState } from 'react'
import { X } from 'lucide-react'
import { createCompany } from '../api/client'

interface Props {
  onClose: () => void
  onCreated: (newId?: number) => void
}

export default function AddCompanyModal({ onClose, onCreated }: Props) {
  const [form, setForm] = useState({
    name: '',
    hp_url: '',
    industry_detail: '',
    description: '',
    notes: '',
  })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name.trim()) return
    setLoading(true)
    try {
      const created = await createCompany(form)
      onCreated(created.id)
      onClose()
    } catch (err: any) {
      alert(`エラー: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 modal-overlay z-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md fade-in" style={{ background: '#fff', border: '1px solid var(--border)', boxShadow: '0 16px 48px rgba(0,0,0,0.12)' }}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5" style={{ borderBottom: '1px solid var(--border-lt)' }}>
          <div>
            <p className="text-[10px] tracking-[0.3em] uppercase mb-0.5" style={{ color: 'var(--text-dim)' }}>New Entry</p>
            <h2 className="text-sm tracking-wide" style={{ color: 'var(--text-pri)' }}>競合会社を追加</h2>
          </div>
          <button
            onClick={onClose}
            className="transition-colors p-1"
            style={{ color: 'var(--text-mute)' }}
            onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-sec)')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-mute)')}
          >
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div>
            <label className="input-label">会社名 <span style={{ color: 'var(--text-mute)' }}>*</span></label>
            <input
              className="input"
              placeholder="株式会社〇〇ジャパン"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="input-label">HP URL</label>
            <input
              className="input"
              type="url"
              placeholder="https://example.com"
              value={form.hp_url}
              onChange={(e) => setForm({ ...form, hp_url: e.target.value })}
            />
          </div>
          <div>
            <label className="input-label">事業種別</label>
            <select
              className="input"
              value={form.industry_detail}
              onChange={(e) => setForm({ ...form, industry_detail: e.target.value })}
            >
              <option value="">— 選択 —</option>
              <option value="技能実習">技能実習</option>
              <option value="特定技能">特定技能</option>
              <option value="高度人材">高度人材</option>
              <option value="技能実習・特定技能">技能実習・特定技能</option>
              <option value="総合人材紹介">総合人材紹介</option>
              <option value="その他">その他</option>
            </select>
          </div>
          <div>
            <label className="input-label">概要・メモ</label>
            <textarea
              className="input resize-none h-20"
              placeholder="会社の概要、特徴など..."
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>

          <div className="flex gap-3 pt-2" style={{ borderTop: '1px solid var(--border-lt)' }}>
            <button type="submit" disabled={loading} className="btn-primary flex-1 justify-center">
              {loading ? '追加中...' : 'Add Company'}
            </button>
            <button type="button" onClick={onClose} className="btn-secondary flex-1 justify-center">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
