"""Pure-function tests for integrations/mediawiki.py's revision-delta math."""
from integrations.mediawiki import _bytes_added


def test_clean_creation_sums_to_final_size():
    # Erissery: created from scratch, every revision by the same user,
    # sizes only ever go up (mod one no-op save) -> signed sum == gross sum.
    revs = [
        {"user": "A", "size": 1586}, {"user": "A", "size": 2773},
        {"user": "A", "size": 3476}, {"user": "A", "size": 3785},
        {"user": "A", "size": 3785}, {"user": "A", "size": 3829},
        {"user": "A", "size": 4066}, {"user": "A", "size": 4302},
        {"user": "A", "size": 4818}, {"user": "A", "size": 5002},
        {"user": "A", "size": 5461}, {"user": "A", "size": 6454},
        {"user": "A", "size": 6552}, {"user": "A", "size": 6549},
        {"user": "A", "size": 6550},
    ]
    assert _bytes_added(revs, base_size=0, username="A") == 6550


def test_own_negative_deltas_are_netted_not_discarded():
    # A user who adds 1000 bytes then trims 400 of their own prose nets
    # 600 -- the old buggy behavior (max(0, delta) per revision) would
    # have counted 1000 and ignored the trim entirely.
    revs = [{"user": "A", "size": 1000}, {"user": "A", "size": 600}]
    assert _bytes_added(revs, base_size=0, username="A") == 600


def test_other_editors_move_the_baseline_but_are_not_credited():
    # Bearcat's -129 edit is real content, not A's -- it must shift the
    # baseline for A's next delta without being added to A's total.
    revs = [
        {"user": "A", "size": 1000},
        {"user": "Bearcat", "size": 871},   # -129, not A's
        {"user": "A", "size": 921},          # +50 off the new baseline
    ]
    assert _bytes_added(revs, base_size=0, username="A") == 1050


def test_net_negative_floors_at_zero():
    # A user who trims more than they add nets negative over the window;
    # bytes_added is never negative.
    revs = [{"user": "A", "size": 1000}, {"user": "A", "size": 200}]
    assert _bytes_added(revs, base_size=1000, username="A") == 0


def test_feminism_in_kerala_matches_the_real_edit_history():
    # Real revision history of https://en.wikipedia.org/wiki/Feminism_in_Kerala
    # (oldest -> newest, from the MediaWiki API): Netha Hussain created the
    # article and made many small edits, some positive and some negative,
    # ending at 18,293 bytes; Bearcat made one unrelated -129 edit partway
    # through. Summing every SIGNED delta of Netha's own revisions (not
    # just the positive ones, and not Bearcat's) gives 18,422 ->
    # floor(18,422 / 1000) = 18 points, not the 19 the old
    # gross-positive-sum bug produced.
    users = ["Netha Hussain"] * 25 + ["Bearcat"] + ["Netha Hussain"] * 13
    sizes = [17899, 17899, 17903, 17922, 17926, 17911, 17919, 17915, 17933,
             17913, 17840, 17844, 17848, 17915, 17914, 17883, 17883, 17869,
             17865, 17822, 17792, 17575, 17596, 17962, 18165, 18036, 18215,
             18260, 18344, 18355, 18361, 18361, 18348, 18348, 18191, 18192,
             18224, 18255, 18293]
    assert len(users) == len(sizes) == 39
    revs = [{"user": u, "size": s} for u, s in zip(users, sizes)]
    assert _bytes_added(revs, base_size=0, username="Netha Hussain") == 18422


def test_chundan_vallam_matches_the_real_edit_history():
    # https://en.wikipedia.org/wiki/Chundan_vallam - Netha Hussain's edits
    # (all on 2026-07-22) monotonically grow the article with no
    # self-reversion, so the signed sum equals net growth: 7,033 (final)
    # - 3,578 (size before her first edit) = 3,455 -> 3 points.
    sizes = [5022, 5324, 5843, 6094, 6095, 6072, 6072, 7033]
    revs = [{"user": "Netha Hussain", "size": s} for s in sizes]
    assert _bytes_added(revs, base_size=3578, username="Netha Hussain") == 3455


def test_kappa_varutthathu_matches_the_real_edit_history():
    # https://ml.wikipedia.org/wiki/കപ്പ_വറുത്തത് - SijiR created the
    # article (base 0) and made almost all the edits; Ranjithsiji and
    # Malikaveedu each made a couple of interleaved edits that shift the
    # baseline but aren't credited/blamed to SijiR.
    users = ['SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR',
             'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR',
             'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR',
             'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR',
             'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR',
             'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR',
             'Ranjithsiji', 'Ranjithsiji', 'SijiR', 'SijiR', 'SijiR', 'SijiR',
             'SijiR', 'Ranjithsiji', 'Malikaveedu']
    sizes = [401, 1253, 2075, 2886, 3348, 3393, 3464, 3693, 3939, 5824, 5865,
             5930, 5974, 6178, 7690, 9155, 9250, 11746, 11782, 11825, 11864,
             11907, 11962, 12234, 12283, 12495, 12516, 12538, 12558, 12558,
             12655, 12659, 12664, 12668, 12674, 12694, 12088, 12097, 12094,
             12118, 12177, 12181, 12149, 12092, 12028, 11634, 11631, 11555,
             11595, 11613, 11689]
    assert len(users) == len(sizes) == 51
    revs = [{"user": u, "size": s} for u, s in zip(users, sizes)]
    assert _bytes_added(revs, base_size=0, username="SijiR") == 11684
