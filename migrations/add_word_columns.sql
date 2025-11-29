-- Migration: Add word_file_path and word_file_size columns to reports table
ALTER TABLE reports ADD COLUMN IF NOT EXISTS word_file_path VARCHAR(255);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS word_file_size INTEGER;
