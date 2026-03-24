-- MarathiMitra Database Schema
-- Run this in Supabase SQL Editor to create all tables
-- ================================================

-- Enable UUID generation
create extension if not exists "uuid-ossp";

-- ================================================
-- PARENTS
-- Parent creates account, manages children
-- ================================================
create table parents (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null unique,
  name text not null,
  created_at timestamptz not null default now()
);

-- Enable RLS
alter table parents enable row level security;
create policy "Parents can read own data" on parents for select using (auth.uid() = id);
create policy "Parents can insert own data" on parents for insert with check (auth.uid() = id);

-- ================================================
-- CHILDREN
-- Parent adds child profiles with age-appropriate settings
-- ================================================
create table children (
  id uuid primary key default uuid_generate_v4(),
  parent_id uuid not null references parents(id) on delete cascade,
  name text not null,
  age int not null check (age between 5 and 12),
  avatar text not null default '🐘',
  current_level int not null default 1 check (current_level between 1 and 4),
  xp_total int not null default 0,
  streak_days int not null default 0,
  streak_last_date date,
  created_at timestamptz not null default now()
);

create index idx_children_parent on children(parent_id);

alter table children enable row level security;
create policy "Parents can manage own children" on children for all using (
  parent_id = auth.uid()
);

-- ================================================
-- LESSONS
-- Structured Marathi lessons in sequence
-- ================================================
create table lessons (
  id uuid primary key default uuid_generate_v4(),
  level int not null check (level between 1 and 4),
  sequence int not null,
  title text not null,           -- e.g. "अभिवादन — Greetings"
  theme text not null,           -- e.g. "greetings", "food", "family"
  vocabulary jsonb not null,     -- [{marathi, english, pronunciation}]
  grammar_note text,             -- optional grammar concept
  quiz_questions jsonb not null, -- [{question, options[], correct_index}]
  unique (level, sequence)
);

-- ================================================
-- CHILD_LESSON_PROGRESS
-- Tracks which lessons each child has completed
-- ================================================
create table child_lesson_progress (
  id uuid primary key default uuid_generate_v4(),
  child_id uuid not null references children(id) on delete cascade,
  lesson_id uuid not null references lessons(id) on delete cascade,
  status text not null default 'not_started' check (status in ('not_started', 'in_progress', 'completed')),
  score int default 0 check (score between 0 and 3),
  completed_at timestamptz,
  unique (child_id, lesson_id)
);

create index idx_child_lesson_child on child_lesson_progress(child_id);

-- ================================================
-- CONVERSATIONS
-- Marathi conversations between child and Mitra
-- ================================================
create table conversations (
  id uuid primary key default uuid_generate_v4(),
  child_id uuid not null references children(id) on delete cascade,
  context text,                  -- lesson theme or free-form topic
  started_at timestamptz not null default now(),
  ended_at timestamptz,          -- null if ongoing
  marathi_ratio float default 0, -- % of child messages in Marathi
  message_count int default 0
);

create index idx_conversations_child on conversations(child_id, started_at desc);

-- ================================================
-- CONVERSATION_MESSAGES
-- Individual messages in each conversation
-- ================================================
create table conversation_messages (
  id uuid primary key default uuid_generate_v4(),
  conversation_id uuid not null references conversations(id) on delete cascade,
  role text not null check (role in ('child', 'mitra')),
  content text not null,
  input_method text not null default 'typed' check (input_method in ('voice', 'typed')),
  created_at timestamptz not null default now()
);

create index idx_messages_conversation on conversation_messages(conversation_id, created_at);

-- ================================================
-- MISSIONS
-- Scenario-based game missions
-- ================================================
create table missions (
  id uuid primary key default uuid_generate_v4(),
  level int not null check (level between 1 and 4),
  title text not null,           -- e.g. "आजीचे स्वयंपाक"
  scenario text not null,        -- roleplay scenario description
  required_vocab jsonb not null, -- vocabulary the mission tests
  xp_reward int not null default 25
);

-- ================================================
-- CHILD_MISSION_PROGRESS
-- Tracks mission completion per child
-- ================================================
create table child_mission_progress (
  id uuid primary key default uuid_generate_v4(),
  child_id uuid not null references children(id) on delete cascade,
  mission_id uuid not null references missions(id) on delete cascade,
  status text not null default 'not_started' check (status in ('not_started', 'in_progress', 'completed')),
  score int default 0,
  completed_at timestamptz,
  unique (child_id, mission_id)
);

create index idx_child_mission_child on child_mission_progress(child_id);
