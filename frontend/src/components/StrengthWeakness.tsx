import { useState } from 'react'
import { Plus, X } from 'lucide-react'
import { parseJsonList } from '../api/client'

interface Props {
  strengths?: string
  weaknesses?: string
  onUpdate: (strengths: string[], weaknesses: string[]) => void
}

function TagEditor({
  items,
  onChange,
  type,
  label,
  placeholder,
}: {
  items: string[]
  onChange: (items: string[]) => void
  type: 'strength' | 'weakness'
  label: string
  placeholder: string
}) {
  const [input, setInput] = useState('')

  const add = () => {
    const v = input.trim()
    if (!v || items.includes(v)) return
    onChange([...items, v])
    setInput('')
  }

  const remove = (i: number) => onChange(items.filter((_, idx) => idx !== i))

  const tagClass = type === 'strength' ? 'tag-strength' : 'tag-weakness'

  return (
    <div>
      <p className="text-xs tracking-widest uppercase mb-2.5 text-neutral-600">{label}</p>
      <div className="flex flex-wrap gap-1.5 mb-3 min-h-[28px]">
        {items.map((item, i) => (
          <span key={i} className={`${tagClass} gap-1.5`}>
            {item}
            <button
              onClick={() => remove(i)}
              className="hover:opacity-60 transition-opacity"
            >
              <X size={10} />
            </button>
          </span>
        ))}
        {items.length === 0 && (
          <span className="text-xs text-neutral-800 tracking-wide">—</span>
        )}
      </div>
      <div className="flex gap-2">
        <input
          className="input text-xs flex-1"
          placeholder={placeholder}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && add()}
        />
        <button
          onClick={add}
          className="btn-secondary px-3 py-2"
        >
          <Plus size={12} />
        </button>
      </div>
    </div>
  )
}

export default function StrengthWeakness({ strengths, weaknesses, onUpdate }: Props) {
  const [str, setStr] = useState<string[]>(parseJsonList(strengths))
  const [weak, setWeak] = useState<string[]>(parseJsonList(weaknesses))
  const [dirty, setDirty] = useState(false)

  const handleStrChange = (v: string[]) => { setStr(v); setDirty(true) }
  const handleWeakChange = (v: string[]) => { setWeak(v); setDirty(true) }
  const handleSave = () => { onUpdate(str, weak); setDirty(false) }

  return (
    <div className="space-y-6">
      <TagEditor
        items={str}
        onChange={handleStrChange}
        type="strength"
        label="Strengths — 強み"
        placeholder="強みを入力 → Enter"
      />
      <div className="border-t border-neutral-900" />
      <TagEditor
        items={weak}
        onChange={handleWeakChange}
        type="weakness"
        label="Weaknesses — 弱み"
        placeholder="弱みを入力 → Enter"
      />
      {dirty && (
        <div className="flex justify-end pt-1">
          <button onClick={handleSave} className="btn-primary text-xs">
            Save
          </button>
        </div>
      )}
    </div>
  )
}
