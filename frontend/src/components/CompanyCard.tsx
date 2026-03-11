import { Link } from 'react-router-dom'
import { ExternalLink, FileText, Video, Link as LinkIcon, ArrowUpRight } from 'lucide-react'
import { Company, parseJsonList } from '../api/client'

interface Props {
  company: Company
  onDelete: (id: number) => void
}

export default function CompanyCard({ company, onDelete }: Props) {
  const strengths = parseJsonList(company.strengths)
  const weaknesses = parseJsonList(company.weaknesses)
  const videoCount = company.files?.filter((f) => f.file_type === 'video').length ?? 0
  const pdfCount = company.files?.filter((f) => f.file_type === 'pdf').length ?? 0
  const linkCount = company.links?.length ?? 0

  return (
    <div className="bg-neutral-950 p-6 group hover:bg-neutral-900 transition-colors duration-300 relative">
      {/* 上部 */}
      <div className="flex items-start justify-between mb-4">
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-medium text-neutral-100 truncate mb-1 tracking-wide">
            {company.name}
          </h3>
          {company.industry_detail && (
            <span className="text-xs tracking-widest uppercase text-neutral-600">
              {company.industry_detail}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1 ml-2 flex-shrink-0">
          {company.hp_url && (
            <a
              href={company.hp_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 text-neutral-700 hover:text-neutral-300 transition-colors"
              title="HP"
              onClick={(e) => e.stopPropagation()}
            >
              <ExternalLink size={13} />
            </a>
          )}
        </div>
      </div>

      {/* 概要 */}
      {company.description && (
        <p className="text-xs text-neutral-600 mb-4 line-clamp-2 leading-relaxed">
          {company.description}
        </p>
      )}

      {/* 強み */}
      {strengths.length > 0 && (
        <div className="mb-3">
          <p className="text-xs tracking-widest uppercase text-neutral-700 mb-1.5">Strengths</p>
          <div className="flex flex-wrap gap-1.5">
            {strengths.slice(0, 3).map((s, i) => (
              <span key={i} className="tag-strength">{s}</span>
            ))}
            {strengths.length > 3 && (
              <span className="text-xs text-neutral-700">+{strengths.length - 3}</span>
            )}
          </div>
        </div>
      )}

      {/* 弱み */}
      {weaknesses.length > 0 && (
        <div className="mb-4">
          <p className="text-xs tracking-widest uppercase text-neutral-800 mb-1.5">Weaknesses</p>
          <div className="flex flex-wrap gap-1.5">
            {weaknesses.slice(0, 2).map((w, i) => (
              <span key={i} className="tag-weakness">{w}</span>
            ))}
            {weaknesses.length > 2 && (
              <span className="text-xs text-neutral-800">+{weaknesses.length - 2}</span>
            )}
          </div>
        </div>
      )}

      {/* ファイル数 */}
      <div className="flex items-center gap-3 text-xs text-neutral-800 mb-5">
        {pdfCount > 0 && (
          <span className="flex items-center gap-1">
            <FileText size={11} />PDF {pdfCount}
          </span>
        )}
        {videoCount > 0 && (
          <span className="flex items-center gap-1">
            <Video size={11} />動画 {videoCount}
          </span>
        )}
        {linkCount > 0 && (
          <span className="flex items-center gap-1">
            <LinkIcon size={11} />Link {linkCount}
          </span>
        )}
      </div>

      {/* アクション */}
      <div className="flex items-center justify-between border-t border-neutral-900 pt-4">
        <button
          onClick={() => onDelete(company.id)}
          className="text-xs text-neutral-800 hover:text-red-900 transition-colors tracking-widest uppercase"
        >
          Delete
        </button>
        <Link
          to={`/companies/${company.id}`}
          className="flex items-center gap-1.5 text-xs text-neutral-500 hover:text-white transition-colors tracking-widest uppercase"
        >
          View <ArrowUpRight size={12} />
        </Link>
      </div>
    </div>
  )
}
