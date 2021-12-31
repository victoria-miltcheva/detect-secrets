import hashlib


def build_automaton(word_list):
    """
    :type word_list: str
    :param word_list: optional word list file for ignoring certain words.

    :rtype: (ahocorasick.Automaton, str)
    :returns: an automaton, and an iterated sha1 hash of the words in the word list.
    """
    # Dynamic import due to optional-dependency
    try:
        import ahocorasick
    except ImportError:  # pragma: no cover
        print('Please install the `pyahocorasick` package to use --word-list')
        raise

    # See https://pyahocorasick.readthedocs.io/en/latest/
    # for more information.
    automaton = ahocorasick.Automaton()
    word_list_hash = hashlib.sha1()

    with open(word_list) as f:
        for line in f.readlines():
            # .lower() to make everything case-insensitive
            line = line.lower().strip()
            if len(line) > 3:
                word_list_hash.update(line.encode('utf-8'))
                automaton.add_word(line, line)

    automaton.make_automaton()

    return (
        automaton,
        word_list_hash.hexdigest(),
    )
