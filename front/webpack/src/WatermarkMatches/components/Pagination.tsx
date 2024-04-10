

export function Pagination({ page, total_pages, setPage }: { page: number, total_pages: number, setPage: (page: number) => void }) {
    /*
    Component to render a pagination control.
    */
    return (
        <div className="pagination">
            <button className="pagination-ctrl button" onClick={() => setPage(page - 1)} disabled={page <= 1}>Previous</button>
            <span className="pagination-page">{page} / {total_pages}</span>
            <button className="pagination-ctrl button" onClick={() => setPage(page + 1)} disabled={page >= total_pages}>Next</button>
        </div>
    );
}
