import { useCallback, useEffect, useRef, useState } from "react";
import { listDocuments, uploadDocument } from "../services/api";
import { STATUS_LABELS, type DocumentStatus } from "../types/api";

interface UploadItem {
  id: string;
  fileName: string;
  date: string;
  status: DocumentStatus;
  error?: string;
}

const isPending = (status: DocumentStatus) => status === "uploaded" || status === "indexing";

export default function UploadPage() {
  const [items, setItems] = useState<UploadItem[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    listDocuments().then((res) => {
      if (!res.ok) return;
      setItems((prev) => {
        const known = new Set(prev.map((i) => i.id));
        const existing = res.data
          .filter((doc) => !known.has(doc.id))
          .map((doc) => ({ id: doc.id, fileName: doc.file_name, date: doc.uploaded_at, status: doc.status }));
        return [...existing, ...prev];
      });
    });
  }, []);

  // ponytail: single poll loop refreshes all pending items instead of one interval per file.
  useEffect(() => {
    if (!items.some((i) => isPending(i.status))) return;
    const timer = setInterval(async () => {
      const res = await listDocuments();
      if (!res.ok) return;
      const byId = new Map(res.data.map((doc) => [doc.id, doc]));
      setItems((prev) =>
        prev.map((item) => {
          const doc = byId.get(item.id);
          return doc ? { ...item, status: doc.status, date: doc.uploaded_at } : item;
        }),
      );
    }, 1500);
    return () => clearInterval(timer);
  }, [items]);

  const addFiles = useCallback((files: FileList | File[]) => {
    for (const file of Array.from(files)) {
      const tempId = crypto.randomUUID();
      setItems((prev) => [{ id: tempId, fileName: file.name, date: new Date().toISOString(), status: "uploaded" }, ...prev]);
      uploadDocument(file).then((res) => {
        setItems((prev) =>
          prev.map((item) => {
            if (item.id !== tempId) return item;
            return res.ok
              ? { id: res.data.id, fileName: res.data.file_name, date: res.data.uploaded_at, status: res.data.status }
              : { ...item, status: "error", error: res.error };
          }),
        );
      });
    }
  }, []);

  return (
    <section>
      <h2>Загрузка документов</h2>
      <div
        data-testid="upload-dropzone"
        className={`dropzone${dragOver ? " dropzone--over" : ""}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          addFiles(e.dataTransfer.files);
        }}
      >
        Перетащите PDF/DOCX сюда или нажмите, чтобы выбрать файлы
        <input
          ref={inputRef}
          type="file"
          multiple
          hidden
          onChange={(e) => {
            if (e.target.files) addFiles(e.target.files);
            e.target.value = "";
          }}
        />
      </div>
      <ul data-testid="doc-list" className="doc-list">
        {items.map((item, i) => (
          <li
            data-testid="upload-item"
            className="doc-list__item"
            key={item.id}
            // stagger entrance top→bottom; nth-child in CSS caps at 5, so drive it by index
            style={{ animationDelay: `${Math.min(i, 12) * 40}ms` }}
          >
            <span className="doc-list__name">{item.fileName}</span>
            <span className="doc-list__date">{new Date(item.date).toLocaleString()}</span>
            <span data-testid="upload-status" className={`status status--${item.status}`}>
              {STATUS_LABELS[item.status]}
              {item.status === "error" && item.error ? `: ${item.error}` : ""}
            </span>
            {item.status !== "error" && (
              // Backend status is discrete (no %), so pending fakes progress via CSS
              // (fill crawls 0→90% while uploaded/indexing); indexed snaps to 100%.
              <div
                data-testid="upload-progress"
                className={`progress${item.status === "indexed" ? " progress--done" : ""}`}
                role="progressbar"
                aria-label={STATUS_LABELS[item.status]}
                aria-valuetext={STATUS_LABELS[item.status]}
              >
                <div className="progress__fill" />
              </div>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
