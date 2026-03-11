import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { ExternalLink, Sparkles, RefreshCw, Edit3, Save, X } from 'lucide-react'
import { getCompany, updateCompany, analyzeCompany, Company } from '../api/client'
import DropZone from '../components/DropZone'
import FileList from '../components/FileList'
import LinkList from '../components/LinkList'
import StrengthWeakness from '../components/StrengthWeakness'

interface Props {
  onChanged?: () => void
}

export default function CompanyDetail({ onChanged }: Props) {
  const { id } = useParams<{ id: string }>()
  const companyId = parseInt(id!)
  const [company, setCompany] = useState<Company | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState<Partial<Company>>({})

  const load = async () => {
    setLoading(true)
    try {
      const data = await getCompany(companyId)
      setCompany(data)
      setEditForm({
        name: data.name,
        hp_url: data.hp_url,
        industry_detail: data.industry_detail,
        description: data.description,
        notes: data.notes,
      })
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [companyId])

  const handleAnalyze = async () => {
    setAnalyzing(true)
    try {
      await analyzeCompany(companyId)
      await load()
    } catch (err: any) {
      alert(`AI分析エラー: ${err.message}`)
    } finally { setAnalyzing(false) }
  }

  const handleSaveEdit = async () => {
    try {
      await updateCompany(companyId, editForm)
      setEditing(false)
      await load()
      onChanged?.()
    } catch (err: any) {
      alert(`保存エラー: ${err.message}`)
    }
  }

  const handleSwUpdate = async (strengths: string[], weaknesses: string[]) => {
    await updateCompany(companyId, {
      strengths: JSON.stringify(strengths),
      weaknesses: JSON.stringify(weaknesses),
    })
    await load()
  }

  if (loading || !company) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{ color: 'var(--text-dim)' }}>
        <RefreshCw size={16} className="animate-spin mr-3" />
        <span className="text-xs tracking-widest uppercase">Loading...</span>
      </div>
    )
  }

  return (
    <div className="px-10 py-10 max-w-4xl">
      {/* ── Company header ──────────────────────────────────────── */}
      <div
        className="p-8 mb-px"
        style={{ background: '#fff', border: '1px solid var(--border)' }}
      >
        {editing ? (
          <div className="space-y-4">
            <input
              className="input text-base font-medium"
              value={editForm.name || ''}
              onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
            />
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="input-label">HP URL</label>
                <input
                  className="input"
                  placeholder="https://"
                  value={editForm.hp_url || ''}
                  onChange={(e) => setEditForm({ ...editForm, hp_url: e.target.value })}
                />
              </div>
              <div>
                <label className="input-label">事業種別</label>
                <select
                  className="input"
                  value={editForm.industry_detail || ''}
                  onChange={(e) => setEditForm({ ...editForm, industry_detail: e.target.value })}
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
            </div>
            <div>
              <label className="input-label">概要</label>
              <textarea
                className="input resize-none h-20"
                value={editForm.description || ''}
                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
              />
            </div>
            <div>
              <label className="input-label">メモ</label>
              <textarea
                className="input resize-none h-14"
                value={editForm.notes || ''}
                onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
              />
            </div>
            <div className="flex gap-3 pt-2">
              <button onClick={handleSaveEdit} className="btn-primary">
                <Save size={13} /> Save
              </button>
              <button onClick={() => setEditing(false)} className="btn-secondary">
                <X size={13} /> Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                {company.industry_detail && (
                  <span
                    className="text-[10px] tracking-widest uppercase px-2.5 py-0.5"
                    style={{ border: '1px solid var(--border)', color: 'var(--text-dim)' }}
                  >
                    {company.industry_detail}
                  </span>
                )}
              </div>
              <h1
                className="text-3xl mb-3"
                style={{
                  fontFamily: '"Cormorant Garamond", serif',
                  fontWeight: 300,
                  letterSpacing: '0.05em',
                  color: 'var(--text-pri)',
                }}
              >
                {company.name}
              </h1>
              {company.hp_url && (
                <a
                  href={company.hp_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-xs tracking-wide transition-colors"
                  style={{ color: 'var(--text-dim)' }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-sec)')}
                  onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-dim)')}
                >
                  <ExternalLink size={11} />
                  {company.hp_url}
                </a>
              )}
              {company.description && (
                <p className="text-sm mt-4 leading-relaxed" style={{ color: 'var(--text-sec)' }}>
                  {company.description}
                </p>
              )}
              {company.notes && (
                <p className="text-xs mt-3 pt-3" style={{ borderTop: '1px solid var(--border-lt)', color: 'var(--text-dim)' }}>
                  {company.notes}
                </p>
              )}
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <button
                onClick={handleAnalyze}
                disabled={analyzing || !company.hp_url}
                className="btn-primary"
                title={!company.hp_url ? 'HP URLを先に登録してください' : 'AI分析'}
              >
                {analyzing ? <RefreshCw size={13} className="animate-spin" /> : <Sparkles size={13} />}
                {analyzing ? 'Analyzing...' : 'AI Analyze'}
              </button>
              <button onClick={() => setEditing(true)} className="btn-secondary">
                <Edit3 size={13} /> Edit
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── AI summary ──────────────────────────────────────────── */}
      {company.ai_summary && (
        <div
          className="px-8 py-5 mb-px"
          style={{ background: '#f8f7f4', border: '1px solid var(--border)', borderTop: 'none' }}
        >
          <div className="flex items-center gap-2 mb-2">
            <Sparkles size={12} style={{ color: 'var(--text-dim)' }} />
            <p className="text-[10px] tracking-widest uppercase" style={{ color: 'var(--text-dim)' }}>
              AI Analysis Summary
            </p>
          </div>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--text-sec)' }}>
            {company.ai_summary}
          </p>
        </div>
      )}

      {/* ── Strengths / Links ───────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-px mb-px" style={{ background: 'var(--border)' }}>
        <div className="p-8" style={{ background: 'var(--bg-base)' }}>
          <p className="section-title">Strengths & Weaknesses</p>
          <StrengthWeakness
            strengths={company.strengths}
            weaknesses={company.weaknesses}
            onUpdate={handleSwUpdate}
          />
        </div>
        <div className="p-8" style={{ background: 'var(--bg-base)' }}>
          <p className="section-title">Links & URLs</p>
          <LinkList
            companyId={companyId}
            links={company.links}
            onChanged={load}
          />
        </div>
      </div>

      {/* ── Files ───────────────────────────────────────────────── */}
      <div className="p-8" style={{ background: '#fff', border: '1px solid var(--border)', borderTop: 'none' }}>
        <div className="flex items-center justify-between mb-6">
          <p className="section-title mb-0">Files & Materials</p>
          <span className="text-xs" style={{ color: 'var(--text-dim)' }}>{company.files.length} files</span>
        </div>
        <DropZone companyId={companyId} onUploaded={load} />
        {company.files.length > 0 && (
          <div className="mt-6 pt-4" style={{ borderTop: '1px solid var(--border-lt)' }}>
            <FileList files={company.files} onDeleted={load} />
          </div>
        )}
      </div>
    </div>
  )
}
