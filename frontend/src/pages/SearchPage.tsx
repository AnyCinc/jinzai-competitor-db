import { useState } from 'react'
import { Search, Sparkles, Plus, ExternalLink, RefreshCw } from 'lucide-react'
import {
  searchCompetitors, analyzeUrl, createCompany,
  SearchResultItem, AnalyzeResponse
} from '../api/client'

interface ResultWithAnalysis extends SearchResultItem {
  analysis?: AnalyzeResponse
  analyzing?: boolean
  saving?: boolean
  saved?: boolean
}

const KEYWORDS = ['外国人材紹介', '技能実習 監理団体', '特定技能 支援機関', '外国人 採用 人材会社']

interface Props {
  onSaved?: () => void
}

export default function SearchPage({ onSaved }: Props) {
  const [query, setQuery] = useState('外国人材紹介')
  const [maxResults, setMaxResults] = useState(10)
  const [results, setResults] = useState<ResultWithAnalysis[]>([])
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState('')

  const handleSearch = async () => {
    setSearching(true); setError(''); setResults([])
    try {
      const res = await searchCompetitors(query, maxResults)
      setResults(res.results)
    } catch (err: any) { setError(err.message) }
    finally { setSearching(false) }
  }

  const handleAnalyze = async (index: number) => {
    setResults((prev) => prev.map((r, i) => i === index ? { ...r, analyzing: true } : r))
    try {
      const analysis = await analyzeUrl(results[index].url)
      setResults((prev) => prev.map((r, i) => i === index ? { ...r, analysis, analyzing: false } : r))
    } catch (err: any) {
      alert(`分析エラー: ${err.message}`)
      setResults((prev) => prev.map((r, i) => i === index ? { ...r, analyzing: false } : r))
    }
  }

  const handleSave = async (index: number) => {
    const item = results[index]
    setResults((prev) => prev.map((r, i) => i === index ? { ...r, saving: true } : r))
    try {
      await createCompany({
        name: item.analysis?.company_name || item.title,
        hp_url: item.url,
        description: item.analysis?.summary || item.snippet,
        strengths: JSON.stringify(item.analysis?.strengths ?? []),
        weaknesses: JSON.stringify(item.analysis?.weaknesses ?? []),
        ai_summary: item.analysis?.summary,
      })
      setResults((prev) => prev.map((r, i) => i === index ? { ...r, saving: false, saved: true } : r))
      onSaved?.()
    } catch (err: any) {
      alert(`保存エラー: ${err.message}`)
      setResults((prev) => prev.map((r, i) => i === index ? { ...r, saving: false } : r))
    }
  }

  return (
    <div className="px-10 py-10 max-w-4xl">
      {/* Header */}
      <div className="mb-10">
        <p className="text-[10px] tracking-[0.5em] uppercase mb-2" style={{ color: 'var(--text-dim)' }}>Discovery</p>
        <h1
          className="text-4xl"
          style={{ fontFamily: '"Cormorant Garamond", serif', fontWeight: 300, letterSpacing: '0.05em', color: 'var(--text-pri)' }}
        >
          Auto Web Search
        </h1>
        <p className="text-xs mt-2 tracking-wide" style={{ color: 'var(--text-dim)' }}>
          キーワードで競合他社を自動検索・AI分析してDBに登録
        </p>
      </div>

      <div style={{ borderTop: '1px solid var(--border)', marginBottom: '2rem' }} />

      {/* Search form */}
      <div className="p-6 mb-8" style={{ background: '#fff', border: '1px solid var(--border)' }}>
        <div className="flex gap-3 mb-4">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-mute)' }} />
            <input
              className="input pl-11"
              placeholder="Search keyword..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>
          <select
            className="input w-24 text-xs"
            value={maxResults}
            onChange={(e) => setMaxResults(Number(e.target.value))}
          >
            <option value={5}>5件</option>
            <option value={10}>10件</option>
            <option value={20}>20件</option>
          </select>
          <button onClick={handleSearch} disabled={searching} className="btn-primary">
            {searching ? <RefreshCw size={13} className="animate-spin" /> : <Search size={13} />}
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          <span className="text-xs tracking-widest uppercase self-center mr-1" style={{ color: 'var(--text-mute)' }}>Quick:</span>
          {KEYWORDS.map((kw) => (
            <button
              key={kw}
              onClick={() => setQuery(kw)}
              className="text-xs px-3 py-1.5 tracking-wide transition-colors"
              style={{
                border: query === kw ? '1px solid #999' : '1px solid var(--border)',
                color: query === kw ? 'var(--text-pri)' : 'var(--text-dim)',
                background: query === kw ? '#f5f4f1' : 'transparent',
              }}
            >
              {kw}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-4 mb-6 text-xs tracking-wide" style={{ border: '1px solid #e8c4c4', background: '#fdf5f5', color: '#a44' }}>
          Error: {error}
        </div>
      )}

      {results.length > 0 && (
        <div>
          <p className="text-xs tracking-widest uppercase mb-4" style={{ color: 'var(--text-dim)' }}>
            {results.length} results
          </p>
          <div style={{ border: '1px solid var(--border)' }}>
            {results.map((item, i) => (
              <div
                key={i}
                className="p-6 transition-colors"
                style={{ borderBottom: i < results.length - 1 ? '1px solid var(--border-lt)' : 'none', background: '#fff' }}
                onMouseEnter={(e) => (e.currentTarget.style.background = '#fcfbf9')}
                onMouseLeave={(e) => (e.currentTarget.style.background = '#fff')}
              >
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div className="min-w-0 flex-1">
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm flex items-center gap-1.5 font-medium mb-1 transition-colors"
                      style={{ color: 'var(--text-pri)' }}
                    >
                      {item.title}
                      <ExternalLink size={11} className="flex-shrink-0" style={{ color: 'var(--text-dim)' }} />
                    </a>
                    <p className="text-xs truncate" style={{ color: 'var(--text-dim)' }}>{item.url}</p>
                  </div>
                  <div className="flex gap-2 flex-shrink-0">
                    {!item.analysis && (
                      <button
                        onClick={() => handleAnalyze(i)}
                        disabled={item.analyzing}
                        className="btn-secondary text-xs"
                      >
                        {item.analyzing ? <RefreshCw size={11} className="animate-spin" /> : <Sparkles size={11} />}
                        {item.analyzing ? 'Analyzing...' : 'AI Analyze'}
                      </button>
                    )}
                    <button
                      onClick={() => handleSave(i)}
                      disabled={item.saving || item.saved}
                      className={item.saved ? 'btn-ghost text-xs cursor-default' : 'btn-primary text-xs'}
                    >
                      {item.saving ? <RefreshCw size={11} className="animate-spin" /> : <Plus size={11} />}
                      {item.saved ? 'Saved' : item.saving ? 'Saving...' : 'Save to DB'}
                    </button>
                  </div>
                </div>

                {item.snippet && (
                  <p className="text-xs mb-4 leading-relaxed" style={{ color: 'var(--text-sec)' }}>{item.snippet}</p>
                )}

                {item.analysis && (
                  <div className="mt-4 pt-4" style={{ borderTop: '1px solid var(--border-lt)' }}>
                    <div className="flex items-center gap-2 mb-3">
                      <Sparkles size={12} style={{ color: 'var(--text-dim)' }} />
                      <span className="text-xs tracking-widest uppercase" style={{ color: 'var(--text-dim)' }}>AI Analysis</span>
                      {item.analysis.company_name && (
                        <span className="text-xs" style={{ color: 'var(--text-sec)' }}>— {item.analysis.company_name}</span>
                      )}
                    </div>
                    {item.analysis.summary && (
                      <p className="text-xs mb-4 leading-relaxed" style={{ color: 'var(--text-sec)' }}>{item.analysis.summary}</p>
                    )}
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <p className="text-xs tracking-widest uppercase mb-2" style={{ color: 'var(--text-dim)' }}>Strengths</p>
                        <div className="flex flex-wrap gap-1.5">
                          {item.analysis.strengths.map((s, si) => (
                            <span key={si} className="tag-strength">{s}</span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="text-xs tracking-widest uppercase mb-2" style={{ color: 'var(--text-dim)' }}>Weaknesses</p>
                        <div className="flex flex-wrap gap-1.5">
                          {item.analysis.weaknesses.map((w, wi) => (
                            <span key={wi} className="tag-weakness">{w}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {!searching && results.length === 0 && (
        <div className="py-24 text-center" style={{ border: '1px dashed var(--border)' }}>
          <Search size={28} className="mx-auto mb-4" style={{ color: 'var(--text-mute)' }} />
          <p className="text-xs tracking-widest uppercase" style={{ color: 'var(--text-mute)' }}>
            Enter a keyword to begin searching
          </p>
        </div>
      )}
    </div>
  )
}
