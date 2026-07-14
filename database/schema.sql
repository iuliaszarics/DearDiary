create table if not exists Users(
    user_id integer primary key autoincrement,
    username text not null unique,
    password_hash text not null,
    created_at datetime default current_timestamp
);
create table if not exists Entries(
    entry_id integer primary key autoincrement,
    user_id integer not null,
    text text not null,
    entry_time datetime default current_timestamp,
    foreign key (user_id) references Users(user_id) on delete cascade
);
create table if not exists Analysis(
    analysis_id integer primary key autoincrement,
    entry_id integer not null,
    model_name text,
    predicted_emotion text,
    confidence real,
    scores_json text,
    task_type text,
    analysis_time datetime default current_timestamp,
    foreign key (entry_id) references Entries(entry_id) on delete cascade
);
create table if not exists DailyEmotionSummary(
    summary_id integer primary key autoincrement,
    user_id integer not null,
    summary_date date not null,
    dominant_emotion text not null,
    emotion_breakdown_json text,
    positivity_score real not null default 0,
    entry_count integer not null default 0,
    latest_entry_preview text,
    summary_text text,
    created_at datetime default current_timestamp,
    foreign key (user_id) references Users(user_id) on delete cascade
);
create table if not exists EntryAdviceHistory(
    advice_history_id integer primary key autoincrement,
    entry_id integer not null,
    advice_key text not null,
    emotion_key text not null,
    title text not null,
    advice_text text not null,
    rationale_text text,
    created_at datetime default current_timestamp,
    foreign key (entry_id) references Entries(entry_id) on delete cascade
);
create table if not exists EntryInsightHistory(
    insight_history_id integer primary key autoincrement,
    entry_id integer not null,
    emotion_bucket text not null,
    title text not null,
    explanation text not null,
    details_json text,
    created_at datetime default current_timestamp,
    foreign key (entry_id) references Entries(entry_id) on delete cascade
);
create index if not exists idx_entries_user on Entries(user_id);
create index if not exists idx_analysis_entry on Analysis(entry_id);
create index if not exists idx_daily_summary_user_date on DailyEmotionSummary(user_id, summary_date);
create index if not exists idx_entry_advice_history_entry on EntryAdviceHistory(entry_id);
