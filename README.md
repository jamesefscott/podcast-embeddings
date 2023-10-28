# Podcast Embeddings
Transcribe and generate embeddings for podcasts.

Stages:
1. Get mp3 URLs and information from RSS feed.
2. Get spotify information.
3. Connect to MongoDB database with existing transcriptions. For any yet to be transcribed:
4. Transcribe with Whisper, to timestamped chunks.
5. Join chunks into "paragraphs" by semantic similarity.
6. Insert paragraph documents with embeddings into db.
