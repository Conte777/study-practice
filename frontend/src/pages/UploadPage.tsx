// Skeleton — FE-02/03 stage fills logic. Wiring left minimal on purpose.
import { STATUS_LABELS } from "../types/api";

export default function UploadPage() {
  return (
    <section>
      <h2>Загрузка документов</h2>
      <div data-testid="upload-dropzone">Перетащите PDF/DOCX сюда</div>
      <ul data-testid="doc-list">
        <li data-testid="upload-item">
          <span>ok.pdf</span>
          <span data-testid="upload-status">{STATUS_LABELS.uploaded}</span>
        </li>
      </ul>
    </section>
  );
}
