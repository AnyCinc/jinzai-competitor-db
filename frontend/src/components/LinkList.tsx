import { useState } from 'react'
import { ExternalLink, Trash2, Plus } from 'lucide-react'
import { CompanyLink, addLink, deleteLink } from '../api/client'

interface Props {
  companyId: number
  links: CompanyLink[]
  onChanged: () => void
}

const LINK_TYPE_LABELS: Record<string, string> = {
  hp: 'HP',
  youtube: 'YouTube',
  sns: 'SNS',
  material: 'Material',
  other: 'Link',
}

export default function LinkList({ companyId, links, onChanged }: Props) {
  const [adding, setAdding] = useState(false)
  const [form, setForm] = useState({ url: '', title: '', link_type: 'other', description: '' })
  const [loading, setLoading] = useState(false)

  const handleAdd = async () => {
    if (!form.url) return
    setLoading(true)
    try {
      await addLink(companyId, form)
      setForm({ url: '', title: '', link_type: 'other', description: '' })
      setAdding(false)
      onChanged()
    } catch (err: any) {
      alert(`エラー: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (link: CompanyLink) => {
    if (!confirm(`「${link.title || link.url}」を削除しますか?`)) return
    await deleteLink(link.id)
    onChanged()
  }

  return (
    <div className="space-y-0">
      {links.map((link) => (
        <div
          key={link.id}
          className="flex items-center gap-3 py-3 border-b border-neutral-900 hover:bg-neutral-900/30 px-1 group transition-colors"
        >
          <span className="text-xs text-neutral-800 tracking-widest uppercase w-16 flex-shrink-0">
            {LINK_TYPE_LABELS[link.link_type || 'other']}
          </span>
          <div className="flex-1 min-w-0">
            <a
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-neutral-400 hover:text-white transition-colors flex items-center gap-1.5 truncate"
            >
              {link.title || link.url}
              <ExternalLink size={11} className="flex-shrink-0" />
            </a>
            {link.description && (
              <p className="text-xs text-neutral-700 mt-0.5">{link.description}</p>
            )}
          </div>
          <button
            onClick={() => handleDelete(link)}
            className="p-1.5 text-neutral-800 hover:text-red-900 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0"
          >
            <Trash2 size={12} />
          </button>
        </div>
      ))}

      {links.length === 0 && !adding && (
        <p className="text-xs text-neutral-800 py-4 tracking-widest uppercase text-center">
          No links added
        </p>
      )}

      {adding ? (
        <div className="border border-neutral-800 bg-neutral-900/50 p-4 space-y-3 mt-2">
          <input
            className="input text-xs"
            placeholder="URL"
            value={form.url}
            onChange={(e) => setForm({ ...form, url: e.target.value })}
          />
          <div className="flex gap-2">
            <input
              className="input text-xs flex-1"
              placeholder="Title (optional)"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
            <select
              className="input text-xs w-28"
              value={form.link_type}
              onChange={(e) => setForm({ ...form, link_type: e.target.value })}
            >
              <option value="hp">HP</option>
              <option value="youtube">YouTube</option>
              <option value="sns">SNS</option>
              <option value="material">資料</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className="flex gap-2">
            <button onClick={handleAdd} disabled={loading} className="btn-primary flex-1 justify-center text-xs">
              {loading ? '...' : 'Add'}
            </button>
            <button onClick={() => setAdding(false)} className="btn-secondary flex-1 justify-center text-xs">
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setAdding(true)}
          className="flex items-center gap-2 text-xs text-neutral-700 hover:text-neutral-400 w-full justify-center py-3 border border-dashed border-neutral-900 hover:border-neutral-700 transition-colors mt-2 tracking-widest uppercase"
        >
          <Plus size={12} />
          Add Link
        </button>
      )}
    </div>
  )
}
