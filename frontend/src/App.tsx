import { useState, useEffect, useCallback } from 'react'
import {
  BrowserRouter, Routes, Route,
  useNavigate, useLocation,
} from 'react-router-dom'
import {
  Plus, Search as SearchIcon, Zap,
  FileText, Link as LinkIcon, RefreshCw, X,
  BookOpen,
} from 'lucide-react'
import { getCompanies, deleteCompany, Company } from './api/client'
import CompanyDetail from './pages/CompanyDetail'
import SearchPage from './pages/SearchPage'
import AddCompanyModal from './components/AddCompanyModal'

/* ── Binding accent colors (rich library tones) ──────────────────── */
const BINDING = [
  '#3b3a36',  // dark walnut
  '#5c6b52',  // forest
  '#6b5a4e',  // leather brown
  '#4a5568',  // slate
  '#7c6f5b',  // tan
  '#4e5d52',  // sage
  '#6d5c5c',  // wine-ish
  '#525e6e',  // steel blue
]

/* ════════════════════════════════════════════════════════════════════
   Book spine item
   ════════════════════════════════════════════════════════════════════ */
interface BookItemProps {
  company: Company
  index: number
  isSelected: boolean
  onClick: () => void
  onDelete: (e: React.MouseEvent) => void
}

function BookItem({ company, index, isSelected, onClick, onDelete }: BookItemProps) {
  const fileCount = company.files?.length ?? 0
  const linkCount = company.links?.length ?? 0
  const color = BINDING[index % BINDING.length]

  return (
    <div
      onClick={onClick}
      className="group relative flex items-stretch cursor-pointer select-none"
      style={{
        background: isSelected ? '#fff' : 'transparent',
        transform: isSelected ? 'translateX(4px)' : 'translateX(0)',
        transition: 'all 0.22s cubic-bezier(0.22, 1, 0.36, 1)',
        boxShadow: isSelected ? '0 1px 4px rgba(0,0,0,0.06)' : 'none',
      }}
      onMouseEnter={(e) => {
        if (!isSelected) {
          e.currentTarget.style.transform = 'translateX(3px)'
          e.currentTarget.style.background = '#f0efec'
        }
      }}
      onMouseLeave={(e) => {
        if (!isSelected) {
          e.currentTarget.style.transform = 'translateX(0)'
          e.currentTarget.style.background = 'transparent'
        }
      }}
    >
      {/* Binding stripe */}
      <div
        style={{
          width: isSelected ? '4px' : '3px',
          flexShrink: 0,
          background: isSelected ? color : color + '40',
          transition: 'all 0.22s ease',
          borderRadius: '0 1px 1px 0',
        }}
      />

      {/* Spine label */}
      <div className="flex-1 px-3.5 py-3 min-w-0">
        <div className="flex items-start justify-between gap-1">
          <div className="min-w-0 flex-1">
            <div className="flex items-baseline gap-1.5">
              <span
                className="text-[9px] tabular-nums flex-shrink-0"
                style={{ color: isSelected ? '#aaa' : '#c5c3be' }}
              >
                {String(index + 1).padStart(2, '0')}
              </span>
              <p
                className="text-[13px] leading-snug truncate"
                style={{
                  color: isSelected ? '#1c1c1a' : '#777',
                  transition: 'color 0.2s',
                  letterSpacing: '0.02em',
                  fontWeight: isSelected ? 400 : 300,
                }}
              >
                {company.name}
              </p>
            </div>
            {company.industry_detail && (
              <p
                className="text-[10px] tracking-widest uppercase mt-0.5 ml-5"
                style={{ color: isSelected ? '#999' : '#c0beb8' }}
              >
                {company.industry_detail}
              </p>
            )}
          </div>
          {/* Delete (hover) */}
          <button
            onClick={onDelete}
            className="opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 mt-0.5 p-0.5"
            style={{ color: '#bbb' }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#c44')}
            onMouseLeave={(e) => (e.currentTarget.style.color = '#bbb')}
            title="削除"
          >
            <X size={9} />
          </button>
        </div>

        {/* File / link micro-stats */}
        {(fileCount > 0 || linkCount > 0) && (
          <div className="flex items-center gap-2 mt-1.5 ml-5">
            {fileCount > 0 && (
              <span className="flex items-center gap-0.5 text-[9px]" style={{ color: isSelected ? '#aaa' : '#d0ceC8' }}>
                <FileText size={8} />{fileCount}
              </span>
            )}
            {linkCount > 0 && (
              <span className="flex items-center gap-0.5 text-[9px]" style={{ color: isSelected ? '#aaa' : '#d0cec8' }}>
                <LinkIcon size={8} />{linkCount}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

/* ── Shelf board ───────────────────────────────────────────────────── */
function ShelfBoard() {
  return (
    <div className="relative mx-0 my-1.5 px-4">
      <div style={{ height: '1px', background: 'linear-gradient(90deg, transparent, #e2e0db 20%, #e2e0db 80%, transparent)' }} />
    </div>
  )
}

/* ════════════════════════════════════════════════════════════════════
   Bookshelf sidebar
   ════════════════════════════════════════════════════════════════════ */
interface BookshelfProps {
  companies: Company[]
  allCount: number
  selectedId: number | null
  isSearchView: boolean
  loading: boolean
  filterTerm: string
  onFilterChange: (s: string) => void
  onSelect: (id: number) => void
  onDelete: (id: number) => void
  onAddClick: () => void
  onSearchNav: () => void
}

function Bookshelf({
  companies, allCount, selectedId, isSearchView, loading,
  filterTerm, onFilterChange,
  onSelect, onDelete, onAddClick, onSearchNav,
}: BookshelfProps) {
  return (
    <aside
      className="flex flex-col h-screen fixed left-0 top-0 z-40"
      style={{
        width: '260px',
        background: '#f5f4f1',
        borderRight: '1px solid #e2e0db',
      }}
    >
      {/* ── Logo ────────────────────────────────────────────────── */}
      <div className="px-5 pt-6 pb-5" style={{ borderBottom: '1px solid #e8e6e2' }}>
        <div className="flex items-center gap-2.5 mb-5">
          <div style={{ width: '12px', height: '12px', border: '1px solid #aaa', transform: 'rotate(45deg)', flexShrink: 0 }} />
          <span className="text-[10px] font-medium" style={{ letterSpacing: '0.35em', color: '#888', textTransform: 'uppercase' }}>
            Competitor DB
          </span>
        </div>

        {/* Filter input */}
        <div className="relative">
          <SearchIcon size={11} className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: '#bbb' }} />
          <input
            className="w-full text-[12px] focus:outline-none transition-colors"
            style={{
              background: '#fff',
              border: '1px solid #ddd',
              color: '#333',
              padding: '8px 28px 8px 28px',
            }}
            placeholder="Filter..."
            value={filterTerm}
            onChange={(e) => onFilterChange(e.target.value)}
            onFocus={(e) => (e.currentTarget.style.borderColor = '#aaa')}
            onBlur={(e) => (e.currentTarget.style.borderColor = '#ddd')}
          />
          {filterTerm && (
            <button
              onClick={() => onFilterChange('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 transition-colors"
              style={{ color: '#bbb' }}
              onMouseEnter={(e) => (e.currentTarget.style.color = '#666')}
              onMouseLeave={(e) => (e.currentTarget.style.color = '#bbb')}
            >
              <X size={10} />
            </button>
          )}
        </div>
      </div>

      {/* ── Shelf label ─────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-5 py-2.5" style={{ borderBottom: '1px solid #eeece8' }}>
        <div className="flex items-center gap-2">
          <BookOpen size={10} style={{ color: '#bbb' }} />
          <span className="text-[9px] tracking-[0.4em] uppercase" style={{ color: '#bbb' }}>
            Library
          </span>
        </div>
        <span className="text-[10px] tabular-nums" style={{ color: '#c5c3be' }}>
          {loading ? '…' : `${allCount} vol.`}
        </span>
      </div>

      {/* ── Book list ───────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto py-1">
        {loading ? (
          <div className="flex items-center justify-center py-16" style={{ color: '#ccc' }}>
            <RefreshCw size={13} className="animate-spin" />
          </div>
        ) : companies.length === 0 ? (
          <div className="px-5 py-10 text-center">
            <p className="text-[11px] tracking-widest uppercase" style={{ color: '#c0beb8' }}>
              {filterTerm ? 'No matches' : 'Empty shelf'}
            </p>
          </div>
        ) : (
          <div>
            {companies.map((company, idx) => (
              <div key={company.id}>
                {idx > 0 && idx % 8 === 0 && <ShelfBoard />}
                <BookItem
                  company={company}
                  index={idx}
                  isSelected={selectedId === company.id}
                  onClick={() => onSelect(company.id)}
                  onDelete={(e) => { e.stopPropagation(); onDelete(company.id) }}
                />
              </div>
            ))}
            <ShelfBoard />
            <div className="h-2" />
          </div>
        )}
      </div>

      {/* ── Footer actions ──────────────────────────────────────── */}
      <div className="p-4 space-y-2" style={{ borderTop: '1px solid #e8e6e2' }}>
        <button
          onClick={onAddClick}
          className="w-full flex items-center justify-center gap-2 py-2.5 text-[11px] font-medium transition-colors duration-200"
          style={{ background: '#2c2c2a', color: '#fff', letterSpacing: '0.2em', textTransform: 'uppercase' }}
          onMouseEnter={(e) => (e.currentTarget.style.background = '#444')}
          onMouseLeave={(e) => (e.currentTarget.style.background = '#2c2c2a')}
        >
          <Plus size={11} />
          Add Company
        </button>

        <button
          onClick={onSearchNav}
          className="w-full flex items-center justify-center gap-2 py-2.5 text-[11px] transition-all duration-200"
          style={{
            border: isSearchView ? '1px solid #888' : '1px solid #ddd',
            color: isSearchView ? '#333' : '#999',
            background: isSearchView ? '#fff' : 'transparent',
            letterSpacing: '0.2em',
            textTransform: 'uppercase',
          }}
          onMouseEnter={(e) => {
            if (!isSearchView) {
              e.currentTarget.style.borderColor = '#aaa'
              e.currentTarget.style.color = '#555'
            }
          }}
          onMouseLeave={(e) => {
            if (!isSearchView) {
              e.currentTarget.style.borderColor = '#ddd'
              e.currentTarget.style.color = '#999'
            }
          }}
        >
          <Zap size={11} />
          Auto Search
        </button>
      </div>
    </aside>
  )
}

/* ── Welcome panel ─────────────────────────────────────────────────── */
function WelcomePanel({ count }: { count: number }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <div className="relative mb-14">
        <div
          className="w-14 h-14 border rotate-45"
          style={{
            borderColor: '#ddd',
            boxShadow: '0 0 40px rgba(0,0,0,0.04)',
          }}
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#ccc' }} />
        </div>
      </div>

      <p className="text-[9px] tracking-[0.6em] uppercase mb-4" style={{ color: '#bbb' }}>
        Intelligence
      </p>
      <h1
        className="mb-8 text-center"
        style={{
          fontFamily: '"Cormorant Garamond", serif',
          fontWeight: 300,
          fontSize: '52px',
          letterSpacing: '0.08em',
          color: '#999',
          lineHeight: 1.15,
        }}
      >
        Competitor<br />Analysis
      </h1>

      <p className="text-[11px] tracking-widest" style={{ color: '#ccc' }}>
        {count > 0
          ? `← ${count} companies on the shelf`
          : '← Add your first company'}
      </p>
    </div>
  )
}

/* ════════════════════════════════════════════════════════════════════
   Layout
   ════════════════════════════════════════════════════════════════════ */
function Layout() {
  const navigate = useNavigate()
  const location = useLocation()

  const [allCompanies, setAllCompanies] = useState<Company[]>([])
  const [filtered, setFiltered] = useState<Company[]>([])
  const [loading, setLoading] = useState(true)
  const [filterTerm, setFilterTerm] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [panelKey, setPanelKey] = useState(0)

  const matchCompany = location.pathname.match(/\/companies\/(\d+)/)
  const selectedId = matchCompany ? parseInt(matchCompany[1]) : null
  const isSearchView = location.pathname === '/search'

  const loadCompanies = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getCompanies()
      setAllCompanies(data)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { loadCompanies() }, [loadCompanies])

  useEffect(() => {
    if (!filterTerm.trim()) {
      setFiltered(allCompanies)
    } else {
      const q = filterTerm.toLowerCase()
      setFiltered(allCompanies.filter(c =>
        c.name.toLowerCase().includes(q) ||
        (c.industry_detail ?? '').toLowerCase().includes(q)
      ))
    }
  }, [allCompanies, filterTerm])

  const handleSelect = (id: number) => {
    setPanelKey(k => k + 1)
    navigate(`/companies/${id}`)
  }
  const handleSearchNav = () => {
    setPanelKey(k => k + 1)
    navigate('/search')
  }
  const handleDelete = async (id: number) => {
    const company = allCompanies.find(c => c.id === id)
    if (!confirm(`「${company?.name}」を削除しますか?`)) return
    try {
      await deleteCompany(id)
      setAllCompanies(prev => prev.filter(c => c.id !== id))
      if (selectedId === id) { setPanelKey(k => k + 1); navigate('/') }
    } catch (err: any) {
      alert(`削除エラー: ${err.message}`)
    }
  }

  return (
    <div className="flex min-h-screen" style={{ background: 'var(--bg-base)' }}>
      <Bookshelf
        companies={filtered}
        allCount={allCompanies.length}
        selectedId={selectedId}
        isSearchView={isSearchView}
        loading={loading}
        filterTerm={filterTerm}
        onFilterChange={setFilterTerm}
        onSelect={handleSelect}
        onDelete={handleDelete}
        onAddClick={() => setShowModal(true)}
        onSearchNav={handleSearchNav}
      />

      <main className="flex-1 overflow-y-auto min-h-screen" style={{ marginLeft: '260px' }}>
        <div key={panelKey} className="book-open min-h-screen">
          <Routes>
            <Route path="/" element={<WelcomePanel count={allCompanies.length} />} />
            <Route path="/companies/:id" element={<CompanyDetail onChanged={loadCompanies} />} />
            <Route path="/search" element={<SearchPage onSaved={loadCompanies} />} />
          </Routes>
        </div>
      </main>

      {showModal && (
        <AddCompanyModal
          onClose={() => setShowModal(false)}
          onCreated={(newId) => {
            loadCompanies()
            setShowModal(false)
            if (newId) { setPanelKey(k => k + 1); navigate(`/companies/${newId}`) }
          }}
        />
      )}
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  )
}
