from sentence_transformers import SentenceTransformer, util
from scipy.signal import argrelextrema
import numpy as np
import logging

logger = logging.getLogger('main-logger')

class SentenceEmbedder:

    def __init__(self, model_name):
        self.model = SentenceTransformer(model_name)
        self.encode = self.model.encode

    def get_sentences(self, transcribed_doc):
        return [chunk["text"].strip() for chunk in transcribed_doc["chunks"]]

    def get_similarities_and_minima(self, transcribed_doc):
        """
        Treating chunks of the transcribed document as sentences, get the
        relative minima in similarity of neighbouring sentences.
        """

        sentences = self.get_sentences(transcribed_doc)
        logger.info('Getting sentence embeddings')
        embeddings = self.model.encode(sentences)
        logger.info('Getting sentence similarities')
        similarity_matrix = util.cos_sim(embeddings, embeddings).numpy()
        pair_wise_similarities = similarity_matrix[
            tuple(np.arange(0, similarity_matrix.shape[0] - 1)),
            (tuple(np.arange(1, similarity_matrix.shape[0]))),
        ]

        relative_minima = argrelextrema(pair_wise_similarities, np.less)[0]
        # Only break at long(ish) sentences.
        relative_minima = [
            k
            for k in relative_minima
            if sentences[k][-1]
            not in "abcdefghijklmnopqrstuvwxyz"  # Don't split mid sentence.
            and len(sentences[k]) > 25  # Don't split on short sentences.
        ]

        logger.info('Relative minima complete.')
        return pair_wise_similarities, relative_minima

    def get_paragraphs_from_similarities(
        self,
        transcribed_doc,
        relative_minima,
        episode_info,
        other_doc_info={},
    ):
        """
        From the minima of neighbouring sentence similarity, splits the episode
        text into 'paragraphs'. Returns a list of paragraphs, with llm embeddings.
        """
        sentences = self.get_sentences(transcribed_doc)
        paragraphs = []
        logger.info('Transforming paragraphs with embedding.')
        episode_doc_idx = 0
        for start_idx, end_idx in zip(
            [-1] + relative_minima, relative_minima + [len(sentences)]
        ):
            para_chunks = transcribed_doc["chunks"][start_idx + 1 : end_idx + 1]
            para_sentences = sentences[start_idx + 1 : end_idx + 1]
            para_text = " ".join(para_sentences)
            paragraphs.append(
                {
                    # "episode": episode_name,
                    "episode_doc_idx": episode_doc_idx,
                    "chunks": para_chunks,
                    # "sentences": para_sentences,
                    # "text": para_text,
                    "embedding": list(self.model.encode(para_text).astype(float)),
                    "episode_info": episode_info,
                    **other_doc_info
                }
            )
            episode_doc_idx +=1
        logger.info('Transform paragraphs with embedding complete.')
        return paragraphs

    def get_paragraphs_with_embeddings(
        self, transcribed_doc, episode_info, other_doc_info={}
    ):
        """
        For the input transcribed document, returns a list of paragraph
        documents with an embedding array per document.
        """
        _, relative_minima = self.get_similarities_and_minima(transcribed_doc)

        paragraphs = self.get_paragraphs_from_similarities(
            transcribed_doc,
            relative_minima,
            episode_info,
            other_doc_info,
        )

        return paragraphs
