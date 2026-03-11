import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { uploadFile } from '../api/client'

interface Props {
  companyId: number
  onUploaded: () => void
}

interface UploadItem {
  name: string
  status: 'uploading' | 'done' | 'error'
  error?: string
}

export default function DropZone({ companyId, onUploaded }: Props) {
  const [items, setItems] = useState<UploadItem[]>([])

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const newItems: UploadItem[] = acceptedFiles.map((f) => ({
        name: f.name,
        status: 'uploading',
      }))
      setItems((prev) => [...newItems, ...prev])

      for (let i = 0; i < acceptedFiles.length; i++) {
        const file = acceptedFiles[i]
        try {
          await uploadFile(companyId, file)
          setItems((prev) =>
            prev.map((item, idx) =>
              item.name === file.name && idx === i ? { ...item, status: 'done' } : item,
            ),
          )
          onUploaded()
        } catch (err: any) {
          setItems((prev) =>
            prev.map((item, idx) =>
              item.name === file.name && idx === i
                ? { ...item, status: 'error', error: err.message }
                : item,
            ),
          )
        }
      }
    },
    [companyId, onUploaded],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'video/mp4': ['.mp4'],
      'video/quicktime': ['.mov'],
      'video/webm': ['.webm'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
    },
    maxSize: 524288000,
  })

  return (
    <div className="space-y-2">
      <div
        {...getRootProps()}
        className={`border border-dashed p-10 text-center cursor-pointer transition-all duration-300 ${
          isDragActive
            ? 'border-neutral-400 bg-neutral-800/30'
            : 'border-neutral-800 hover:border-neutral-600 hover:bg-neutral-900/50'
        }`}
      >
        <input {...getInputProps()} />
        <Upload
          size={28}
          className={`mx-auto mb-4 transition-colors ${
            isDragActive ? 'text-neutral-200' : 'text-neutral-700'
          }`}
        />
        <p className={`text-sm tracking-wide transition-colors ${isDragActive ? 'text-neutral-200' : 'text-neutral-600'}`}>
          {isDragActive ? 'Drop here' : 'Drag & Drop'}
        </p>
        <p className="text-xs text-neutral-800 mt-1.5 tracking-widest uppercase">
          PDF · MP4 · MOV · WEBM · JPG · PNG — max 500MB
        </p>
        <button className="mt-4 text-xs text-neutral-700 hover:text-neutral-400 tracking-widest uppercase transition-colors">
          or click to browse
        </button>
      </div>

      {items.length > 0 && (
        <div className="space-y-1 mt-2">
          {items.slice(0, 5).map((item, i) => (
            <div
              key={i}
              className="flex items-center gap-3 text-xs px-4 py-2.5 bg-neutral-900 border border-neutral-800"
            >
              {item.status === 'uploading' && (
                <Loader2 size={13} className="text-neutral-500 animate-spin flex-shrink-0" />
              )}
              {item.status === 'done' && (
                <CheckCircle size={13} className="text-neutral-400 flex-shrink-0" />
              )}
              {item.status === 'error' && (
                <XCircle size={13} className="text-neutral-600 flex-shrink-0" />
              )}
              <span className="truncate text-neutral-500">{item.name}</span>
              {item.status === 'done' && (
                <span className="ml-auto text-neutral-700 tracking-widest uppercase flex-shrink-0">
                  Uploaded
                </span>
              )}
              {item.error && (
                <span className="text-xs text-neutral-700 ml-auto flex-shrink-0">{item.error}</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
