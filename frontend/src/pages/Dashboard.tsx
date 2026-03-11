import { useEffect, useState } from 'react'
import { Plus, Search, RefreshCw } from 'lucide-react'
import { getCompanies, deleteCompany, Company } from '../api/client'
import CompanyCard from '../components/CompanyCard'
import AddCompanyModal from '../components/AddCompanyModal'

export default function Dashboard() {
  const [companies, setCompanies] = useState<Company[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const data = await getCompanies(search || undefined)
      setCompanies(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [search])

  const handleDelete = async (id: number) => {
    const company = companies.find((c) => c.id === id)
    if (!confirm(`「${company?.name}」を削除しますか?`)) return
    try {
      await deleteCompany(id)
      setCompanies((prev) => prev.filter((c) => c.id !== id))
    } catch (err: any) {
      alert(`削除エラー: ${err.message}`)
    }
  }

  return (
    <div className="fade-in">
      {/* ページヘッダー */}
      <div className="flex items-end justify-between mb-10 pt-4">
        <div>
          <p className="text-xs tracking-[0.4em] uppercase text-neutral-600 mb-2">Intelligence</p>
          <h1 className="font-serif text-4xl text-white tracking-wide" style={{ fontFamily: '"Cormorant Garamond", serif', fontWeight: 300 }}>
            Competitor Analysis
          </h1>
          <p className="text-xs text-neutral-700 mt-2 tracking-widest">
            {companies.length} companies registered
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="btn-primary"
        >
          <Plus size={13} />
          Add Company
        </button>
      </div>

      {/* 区切り線 */}
      <div className="border-t border-neutral-800 mb-8" />

      {/* 検索バー */}
      <div className="relative mb-8">
        <Search size={14} className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-700" />
        <input
          className="input pl-11 bg-neutral-950 border-neutral-800 focus:border-neutral-600"
          placeholder="Search companies..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        {search && (
          <button
            onClick={() => setSearch('')}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-neutral-700 hover:text-neutral-400 transition-colors"
          >
            ✕
          </button>
        )}
      </div>

      {/* 会社グリッド */}
      {loading ? (
        <div className="flex items-center justify-center py-24 text-neutral-700">
          <RefreshCw size={16} className="animate-spin mr-3" />
          <span className="text-xs tracking-widest uppercase">Loading...</span>
        </div>
      ) : companies.length === 0 ? (
        <div className="text-center py-24 border border-dashed border-neutral-800">
          <p className="text-neutral-700 text-sm mb-6 tracking-wide">
            {search ? 'No results found' : 'No companies registered yet'}
          </p>
          {!search && (
            <button onClick={() => setShowModal(true)} className="btn-secondary">
              Add First Company
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-px bg-neutral-800">
          {companies.map((company) => (
            <CompanyCard
              key={company.id}
              company={company}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {showModal && (
        <AddCompanyModal
          onClose={() => setShowModal(false)}
          onCreated={load}
        />
      )}
    </div>
  )
}
