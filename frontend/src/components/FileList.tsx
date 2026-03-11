import { useState } from 'react'
import { FileText, Video, Image, Download, Trash2, Play, Eye } from 'lucide-react'
import { CompanyFile, deleteFile, formatSize } from '../api/client'

interface Props {
  files: CompanyFile[]
  onDeleted: () => void
}

const FILE_ICONS = {
  pdf: <FileText size={15} className="text-neutral-500" />,
  video: <Video size={15} className="text-neutral-500" />,
  image: <Image size={15} className="text-neutral-500" />,
}

export default function FileList({ files, onDeleted }: Props) {
  const [preview, setPreview] = useState<CompanyFile | null>(null)

  const handleDelete = async (file: CompanyFile) => {
    if (!confirm(`「${file.original_name}」を削除しますか?`)) return
    try {
      await deleteFile(file.id)
      onDeleted()
    } catch (err: any) {
      alert(`削除エラー: ${err.message}`)
    }
  }

  if (files.length === 0) {
    return (
      <p className="text-xs text-neutral-800 text-center py-6 tracking-widest uppercase">
        No files uploaded
      </p>
    )
  }

  return (
    <>
      <div className="divide-y divide-neutral-900">
        {files.map((file) => (
          <div
            key={file.id}
            className="flex items-center gap-3 py-3 hover:bg-neutral-900/50 px-1 group transition-colors"
          >
            <div className="flex-shrink-0">
              {FILE_ICONS[file.file_type as keyof typeof FILE_ICONS] ?? (
                <FileText size={15} className="text-neutral-700" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-neutral-300 truncate">{file.original_name}</p>
              <p className="text-xs text-neutral-700 mt-0.5">
                {formatSize(file.size)} · {new Date(file.created_at).toLocaleDateString('ja-JP')}
              </p>
            </div>
            <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
              {(file.file_type === 'pdf' || file.file_type === 'video') && (
                <button
                  onClick={() => setPreview(file)}
                  className="p-2 text-neutral-700 hover:text-neutral-300 transition-colors"
                  title="Preview"
                >
                  {file.file_type === 'video' ? <Play size={13} /> : <Eye size={13} />}
                </button>
              )}
              <a
                href={`/api/files/${file.id}/download`}
                className="p-2 text-neutral-700 hover:text-neutral-300 transition-colors"
                title="Download"
              >
                <Download size={13} />
              </a>
              <button
                onClick={() => handleDelete(file)}
                className="p-2 text-neutral-800 hover:text-red-900 transition-colors"
                title="Delete"
              >
                <Trash2 size={13} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* プレビューモーダル */}
      {preview && (
        <div
          className="fixed inset-0 modal-overlay z-50 flex items-center justify-center p-4"
          onClick={() => setPreview(null)}
        >
          <div
            className="bg-neutral-900 border border-neutral-800 overflow-hidden max-w-4xl w-full max-h-[90vh] fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-neutral-800">
              <p className="text-xs text-neutral-400 truncate tracking-wide">{preview.original_name}</p>
              <button
                onClick={() => setPreview(null)}
                className="text-neutral-700 hover:text-neutral-300 transition-colors ml-4 text-xs tracking-widest"
              >
                CLOSE
              </button>
            </div>
            <div className="overflow-auto max-h-[82vh]">
              {preview.file_type === 'video' ? (
                <video
                  src={`/api/files/${preview.id}/preview`}
                  controls
                  autoPlay
                  className="w-full"
                />
              ) : preview.file_type === 'pdf' ? (
                <iframe
                  src={`/api/files/${preview.id}/preview`}
                  className="w-full"
                  style={{ height: '78vh' }}
                  title={preview.original_name}
                />
              ) : null}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
