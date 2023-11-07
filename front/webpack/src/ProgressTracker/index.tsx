import React from "react";

interface ProgressStatus {
    status: string;
    log: {
        infos?: string[];
        progress?: {context: string, current: number, total: number}[];
        errors?: string[];
    };
}

export function TaskProgressTracker (props: {tracking_url: string}) {
    const [status, setStatus] = React.useState<ProgressStatus | null>(null);
    const [is_finished, setFinished] = React.useState(false);
    const [error, setError] = React.useState<string | null>(null);

    // regular polling using setTimeout after results
    const poll = React.useCallback(() => {
        fetch(props.tracking_url)
            .then(response => response.json())
            .then(data => {
                setStatus(data);
                if (data.status === "finished") {
                    setFinished(true);
                } else {
                    setTimeout(poll, 1000);
                }
            })
            .catch(error => {
                setError(error.toString());
                setTimeout(poll, 1000);
            });
    }, [props.tracking_url]);

    React.useEffect(() => {
        poll();
    }, [poll]);

    if (error)
        return <div className="tck-progress"><div className="tck-error">{error}</div></div>;

    if (is_finished) {
        window.location.reload();
        return <div className="tck-progress">Done!</div>;
    }

    if (status === null)
        return <div className="tck-progress">Loading...</div>;

    return (<div className="tck-progress">
        <p>Status: {status.status}</p>
        {status.log?.progress && 
        <div className="tck-bar-list">
            {status.log.progress.map((progress, i) => 
            <div key={i}>
                <span className="label">{progress.context} {progress.current}/{progress.total}</span> 
                <progress className="bar" value={progress.current} max={progress.total} /> 
            </div>)}
        </div>}
        <pre>{status.status == "PENDING" ? "Waiting for worker..." : status.log?.infos?.join("\n")}</pre>
    </div>);
}