import { useState, useCallback, useEffect } from 'react'
import imageCompression from 'browser-image-compression'
import './ImageUpload.css'

interface ImageUploadProps {
  onImageReady: (base64: string) => void
  loading?: boolean
  resetKey?: number
}

export default function ImageUpload({ onImageReady, loading, resetKey = 0 }: ImageUploadProps) {
  const [preview, setPreview] = useState<string>('')

  useEffect(() => {
    setPreview('')
  }, [resetKey])

  const handleFile = useCallback(async (file: File) => {
    const options = { maxSizeMB: 1, maxWidthOrHeight: 1920, useWebWorker: true }
    const compressed = await imageCompression(file, options)
    const reader = new FileReader()
    reader.onload = (e) => {
      const base64 = (e.target?.result as string).split(',')[1]
      setPreview(e.target?.result as string)
      onImageReady(base64)
    }
    reader.readAsDataURL(compressed)
  }, [onImageReady])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  return (
    <div className="image-upload">
      {preview ? (
        <div className="preview-container">
          <img src={preview} alt="preview" className="preview-img" />
          {loading && <div className="scan-overlay"><div className="scan-line" /></div>}
        </div>
      ) : (
        <label className="upload-area">
          <input type="file" accept="image/*" capture="environment" onChange={handleChange} hidden />
          <div className="upload-icon">📷</div>
          <p>拍照或选择食物照片</p>
        </label>
      )}
    </div>
  )
}
