"""Frequency tags (core, common, rare) from wordfreq's Zipf frequency, for importers.

Needs `pip install "wordfreq[mecab]"` (the mecab extra is for Japanese and
Korean). wordfreq's data is CC BY-SA 4.0.
"""
import sys

CORE, COMMON = 4.5, 3.5  # Zipf: core at 4.5 and above, common from 3.5, rare below


def tag(zipf):
    return "core" if zipf >= CORE else "common" if zipf >= COMMON else "rare"


def zipf_tagger(lang):
    """A function word -> 'core' | 'common' | 'rare' for wordfreq language code lang."""
    try:
        from wordfreq import zipf_frequency
    except ImportError:
        sys.exit('needs wordfreq: pip install "wordfreq[mecab]"')
    return lambda word: tag(zipf_frequency(word, lang))
