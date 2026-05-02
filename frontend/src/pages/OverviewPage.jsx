import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { events as eventsApi, allocationCategories, participants as participantsApi, notes as notesApi } from '../services/api';
import { useDateFormat } from '../hooks/useDateFormat';
import { useI18n } from '../hooks/useI18n';
import AllocationBoard from '../components/AllocationBoard';
import Wordmark from '../components/Wordmark';
import ThemeToggle from '../components/ThemeToggle';
import TranslatedError from '../components/TranslatedError';

export default function OverviewPage() {
  const { eventId, categoryId } = useParams();
  const [event, setEvent] = useState(null);
  const [category, setCategory] = useState(null);
  const [participantList, setParticipantList] = useState([]);
  const [noteCounts, setNoteCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [includeNotes, setIncludeNotes] = useState(false);
  const { formatDate } = useDateFormat();
  const { t } = useI18n();

  useEffect(() => { loadAll(); }, [eventId, categoryId]);

  const loadAll = async () => {
    try {
      const [ev, cats, parts] = await Promise.all([
        eventsApi.get(eventId),
        allocationCategories.list(eventId),
        participantsApi.list(eventId),
      ]);
      setEvent(ev); setParticipantList(parts);
      const cat = cats.find(c => String(c.id) === categoryId);
      if (!cat) { setError(t('overview.group_not_found')); setLoading(false); return; }
      setCategory(cat);
      notesApi.counts(eventId).then(setNoteCounts).catch(() => {});
    } catch (err) { setError(err); }
    finally { setLoading(false); }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center"
           style={{ backgroundColor: 'var(--app-bg)' }}>
        <p style={{ color: 'var(--text-subtle)' }}>{t('common.loading')}</p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="min-h-screen p-6" style={{ backgroundColor: 'var(--app-bg)' }}>
        <TranslatedError err={error} className="text-sm rounded-card p-3" />
      </div>
    );
  }

  const dateRange = event?.start_date
    ? `${formatDate(event.start_date)}${event.end_date ? ' – ' + formatDate(event.end_date) : ''}`
    : '';

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--app-bg)' }}>
      {/*
        Header — dark-navy strip on screen, light strip in print.
        In dark theme the strip stays the same navy (intentional: it's the
        branded chrome; the main surface below flips with the theme).
      */}
      <div className="bg-deep-navy text-white px-6 py-3 print:bg-white print:text-deep-navy print:border-b print:border-gray-200">
        <div className="flex items-center gap-3 mb-0.5">
          <img src="/logogram.svg" alt="Moimio" className="w-6 h-6 print:hidden" />
          <h1 className="font-heading font-extrabold text-base truncate">{event?.name}</h1>
          <span className="ml-auto hidden md:inline print:hidden">
            <Wordmark size="sm" />
          </span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="font-heading font-bold text-sm text-white/80 print:text-gray-600">
              {category?.name} {t('overview.overview')}
            </span>
            {dateRange && (
              <span className="text-[10px] text-white/40 print:text-gray-400">{dateRange}</span>
            )}
            {event?.location && (
              <span className="text-[10px] text-white/40 print:text-gray-400">{event.location}</span>
            )}
          </div>
          <div className="flex items-center gap-4 print:hidden">
            <label className="flex items-center gap-1.5 text-[10px] text-white/50 cursor-pointer">
              <input type="checkbox" checked={includeNotes}
                     onChange={e => setIncludeNotes(e.target.checked)}
                     className="h-3 w-3 rounded" />
              {t('overview.show_notes')}
            </label>
            <button onClick={() => window.print()}
                    className="text-[10px] text-white/50 hover:text-white">
              {t('organise.print')}
            </button>
            <button onClick={() => window.close()}
                    className="text-[10px] text-white/50 hover:text-white">
              {t('overview.close_tab')}
            </button>
            <ThemeToggle tone="sidebar" />
          </div>
        </div>
      </div>
      <div className="p-4">
        <AllocationBoard eventId={eventId} category={category}
                         participantList={participantList} noteCounts={noteCounts}
                         isAdmin={true} onDataChange={loadAll}
                         isOverview={true} includeNotes={includeNotes} />
      </div>
    </div>
  );
}
