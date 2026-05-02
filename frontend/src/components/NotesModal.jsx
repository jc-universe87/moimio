import { useState, useEffect } from 'react';
import { notes as notesApi } from '../services/api';
import { useConfirmOverlay } from './ConfirmOverlay';
import { useI18n } from '../hooks/useI18n';
import TranslatedError from './TranslatedError';

export default function NotesModal({ entityType, entityId, entityName, onClose }) {
  const [notesList, setNotesList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newNote, setNewNote] = useState('');
  const [isPublished, setIsPublished] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const { confirm, ConfirmOverlay } = useConfirmOverlay();
  const { t } = useI18n();

  useEffect(() => { loadNotes(); }, [entityType, entityId]);

  const loadNotes = async () => {
    try {
      const data = await notesApi.list(entityType, entityId);
      setNotesList(data);
    } catch (err) { setError(err); }
    finally { setLoading(false); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    setSubmitting(true); setError(null);
    try {
      await notesApi.create({ notable_type: entityType, notable_id: entityId, content: newNote.trim(), is_published: isPublished });
      setNewNote(''); setIsPublished(false);
      await loadNotes();
    } catch (err) { setError(err); }
    finally { setSubmitting(false); }
  };

  const handleDelete = async (noteId) => {
    const ok = await confirm({ title: t('notes.delete.title'), message: t('notes.delete.message'), confirmLabel: t('common.delete'), danger: true });
    if (!ok) return;
    try { await notesApi.delete(noteId); await loadNotes(); }
    catch (err) { setError(err); }
  };

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-card-solid rounded-xl shadow-lg w-full max-w-lg max-h-[80vh] flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="px-5 py-3 border-b border-card flex items-center justify-between shrink-0">
          <div>
            <h3 className="font-heading font-bold text-body">{t('notes.title')}</h3>
            <p className="text-xs text-subtle">{entityName}</p>
          </div>
          <button onClick={onClose} className="text-subtle hover:text-muted text-lg">✕</button>
        </div>

        <TranslatedError err={error} className="mx-5 mt-3 text-xs rounded-lg p-2" />

        <div className="flex-1 overflow-y-auto px-5 py-3">
          {loading ? (
            <p className="text-subtle text-sm">{t('common.loading')}</p>
          ) : notesList.length === 0 ? (
            <p className="text-subtle text-sm text-center py-4">{t('notes.empty')}</p>
          ) : (
            <div className="space-y-3">
              {notesList.map(note => (
                <div key={note.id} className={`rounded-lg p-3 ${note.is_published ? 'bg-accent-tint border border-accent' : 'bg-neutral-tint border border-card'}`}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <p className="text-sm text-body whitespace-pre-wrap">{note.content}</p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${note.is_published ? 'bg-accent-tint text-accent' : 'bg-neutral-tint text-muted'}`}>
                          {note.is_published ? t('notes.team') : t('notes.private')}
                        </span>
                        <span className="text-[10px] text-subtle">{new Date(note.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                    <button onClick={() => handleDelete(note.id)} className="text-xs text-alert hover:text-alert shrink-0">✕</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="px-5 py-3 border-t border-card shrink-0">
          <form onSubmit={handleSubmit}>
            <textarea value={newNote} onChange={e => setNewNote(e.target.value)}
              placeholder={t('notes.write')} rows={2}
              className="w-full border border-card rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-steel-blue resize-none mb-2" />
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-1.5 text-xs text-muted cursor-pointer">
                <input type="checkbox" checked={isPublished} onChange={e => setIsPublished(e.target.checked)}
                  className="h-3.5 w-3.5 text-accent border-card rounded focus:ring-steel-blue" />
                {t('notes.share')}
              </label>
              <button type="submit" disabled={submitting || !newNote.trim()}
                className="bg-steel-blue text-white text-xs font-semibold px-3 py-1.5 rounded-lg hover:bg-mid-navy transition-colors disabled:opacity-50">
                {submitting ? t('notes.adding') : t('notes.add')}
              </button>
            </div>
          </form>
        </div>
      </div>
      <ConfirmOverlay />
    </div>
  );
}
