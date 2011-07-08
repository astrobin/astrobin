/* This file was generated automatically by the Snowball to ISO C++ compiler */

#include <limits.h>
#include "german2.h"

static const symbol s_pool[] = {
#define s_0_1 0
'a', 'e',
#define s_0_2 2
'o', 'e',
#define s_0_3 4
'q', 'u',
#define s_0_4 6
'u', 'e',
#define s_0_5 8
0xC3, 0x9F,
#define s_1_1 10
'U',
#define s_1_2 11
'Y',
#define s_1_3 12
0xC3, 0xA4,
#define s_1_4 14
0xC3, 0xB6,
#define s_1_5 16
0xC3, 0xBC,
#define s_2_0 s_2_1
#define s_2_1 18
'e', 'm',
#define s_2_2 20
'e', 'n',
#define s_2_3 22
'e', 'r', 'n',
#define s_2_4 s_2_3
#define s_2_5 (s_2_6 + 1)
#define s_2_6 25
'e', 's',
#define s_3_0 27
'e', 'n',
#define s_3_1 29
'e', 'r',
#define s_3_2 (s_3_3 + 1)
#define s_3_3 31
'e', 's', 't',
#define s_4_0 34
'i', 'g',
#define s_4_1 36
'l', 'i', 'c', 'h',
#define s_5_0 40
'e', 'n', 'd',
#define s_5_1 43
'i', 'g',
#define s_5_2 45
'u', 'n', 'g',
#define s_5_3 48
'l', 'i', 'c', 'h',
#define s_5_4 52
'i', 's', 'c', 'h',
#define s_5_5 56
'i', 'k',
#define s_5_6 58
'h', 'e', 'i', 't',
#define s_5_7 62
'k', 'e', 'i', 't',
};


static const struct among a_0[6] =
{
/*  0 */ { 0, 0, -1, 6},
/*  1 */ { 2, s_0_1, 0, 2},
/*  2 */ { 2, s_0_2, 0, 3},
/*  3 */ { 2, s_0_3, 0, 5},
/*  4 */ { 2, s_0_4, 0, 4},
/*  5 */ { 2, s_0_5, 0, 1}
};


static const struct among a_1[6] =
{
/*  0 */ { 0, 0, -1, 6},
/*  1 */ { 1, s_1_1, 0, 2},
/*  2 */ { 1, s_1_2, 0, 1},
/*  3 */ { 2, s_1_3, 0, 3},
/*  4 */ { 2, s_1_4, 0, 4},
/*  5 */ { 2, s_1_5, 0, 5}
};


static const struct among a_2[7] =
{
/*  0 */ { 1, s_2_0, -1, 2},
/*  1 */ { 2, s_2_1, -1, 1},
/*  2 */ { 2, s_2_2, -1, 2},
/*  3 */ { 3, s_2_3, -1, 1},
/*  4 */ { 2, s_2_4, -1, 1},
/*  5 */ { 1, s_2_5, -1, 3},
/*  6 */ { 2, s_2_6, 5, 2}
};


static const struct among a_3[4] =
{
/*  0 */ { 2, s_3_0, -1, 1},
/*  1 */ { 2, s_3_1, -1, 1},
/*  2 */ { 2, s_3_2, -1, 2},
/*  3 */ { 3, s_3_3, 2, 1}
};


static const struct among a_4[2] =
{
/*  0 */ { 2, s_4_0, -1, 1},
/*  1 */ { 4, s_4_1, -1, 1}
};


static const struct among a_5[8] =
{
/*  0 */ { 3, s_5_0, -1, 1},
/*  1 */ { 2, s_5_1, -1, 2},
/*  2 */ { 3, s_5_2, -1, 1},
/*  3 */ { 4, s_5_3, -1, 3},
/*  4 */ { 4, s_5_4, -1, 2},
/*  5 */ { 2, s_5_5, -1, 2},
/*  6 */ { 4, s_5_6, -1, 3},
/*  7 */ { 4, s_5_7, -1, 4}
};

static const unsigned char g_v[] = { 17, 65, 16, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 32, 8 };

static const unsigned char g_s_ending[] = { 117, 30, 5 };

static const unsigned char g_st_ending[] = { 117, 30, 4 };

static const symbol s_0[] = { 'U' };
static const symbol s_1[] = { 'Y' };
static const symbol s_2[] = { 's', 's' };
static const symbol s_3[] = { 0xC3, 0xA4 };
static const symbol s_4[] = { 0xC3, 0xB6 };
static const symbol s_5[] = { 0xC3, 0xBC };
static const symbol s_6[] = { 'y' };
static const symbol s_7[] = { 'u' };
static const symbol s_8[] = { 'a' };
static const symbol s_9[] = { 'o' };
static const symbol s_10[] = { 'u' };
static const symbol s_11[] = { 'n', 'i', 's' };
static const symbol s_12[] = { 'i', 'g' };
static const symbol s_13[] = { 'e', 'r' };
static const symbol s_14[] = { 'e', 'n' };

int Xapian::InternalStemGerman2::r_prelude() { /* forwardmode */
    int among_var;
    {   int c_test1 = c; /* test, line 35 */
        while(1) { /* repeat, line 35 */
            int c2 = c;
            while(1) { /* goto, line 35 */
                int c3 = c;
                if (in_grouping_U(g_v, 97, 252, 0)) goto lab1; /* grouping v, line 36 */
                bra = c; /* [, line 36 */
                {   int c4 = c; /* or, line 36 */
                    if (c == l || p[c] != 'u') goto lab3;
                    c++;
                    ket = c; /* ], line 36 */
                    if (in_grouping_U(g_v, 97, 252, 0)) goto lab3; /* grouping v, line 36 */
                    {   int ret = slice_from_s(1, s_0); /* <-, line 36 */
                        if (ret < 0) return ret;
                    }
                    goto lab2;
                lab3:
                    c = c4;
                    if (c == l || p[c] != 'y') goto lab1;
                    c++;
                    ket = c; /* ], line 37 */
                    if (in_grouping_U(g_v, 97, 252, 0)) goto lab1; /* grouping v, line 37 */
                    {   int ret = slice_from_s(1, s_1); /* <-, line 37 */
                        if (ret < 0) return ret;
                    }
                }
            lab2:
                c = c3;
                break;
            lab1:
                c = c3;
                {   int ret = skip_utf8(p, c, 0, l, 1);
                    if (ret < 0) goto lab0;
                    c = ret; /* goto, line 35 */
                }
            }
            continue;
        lab0:
            c = c2;
            break;
        }
        c = c_test1;
    }
    while(1) { /* repeat, line 40 */
        int c5 = c;
        bra = c; /* [, line 41 */
        among_var = find_among(s_pool, a_0, 6, 0, 0); /* substring, line 41 */
        if (!(among_var)) goto lab4;
        ket = c; /* ], line 41 */
        switch(among_var) { /* among, line 41 */
            case 0: goto lab4;
            case 1:
                {   int ret = slice_from_s(2, s_2); /* <-, line 42 */
                    if (ret < 0) return ret;
                }
                break;
            case 2:
                {   int ret = slice_from_s(2, s_3); /* <-, line 43 */
                    if (ret < 0) return ret;
                }
                break;
            case 3:
                {   int ret = slice_from_s(2, s_4); /* <-, line 44 */
                    if (ret < 0) return ret;
                }
                break;
            case 4:
                {   int ret = slice_from_s(2, s_5); /* <-, line 45 */
                    if (ret < 0) return ret;
                }
                break;
            case 5:
                {   int ret = skip_utf8(p, c, 0, l, + 2); /* hop, line 46 */
                    if (ret < 0) goto lab4;
                    c = ret;
                }
                break;
            case 6:
                {   int ret = skip_utf8(p, c, 0, l, 1);
                    if (ret < 0) goto lab4;
                    c = ret; /* next, line 47 */
                }
                break;
        }
        continue;
    lab4:
        c = c5;
        break;
    }
    return 1;
}

int Xapian::InternalStemGerman2::r_mark_regions() { /* forwardmode */
    I_p1 = l; /* p1 = <integer expression>, line 55 */
    I_p2 = l; /* p2 = <integer expression>, line 56 */
    {   int c_test1 = c; /* test, line 58 */
        {   int ret = skip_utf8(p, c, 0, l, + 3); /* hop, line 58 */
            if (ret < 0) return 0;
            c = ret;
        }
        I_x = c; /* setmark x, line 58 */
        c = c_test1;
    }
    {   int ret = out_grouping_U(g_v, 97, 252, 1); /* gopast */ /* grouping v, line 60 */
        if (ret < 0) return 0;
        c += ret;
    }
    {   int ret = in_grouping_U(g_v, 97, 252, 1); /* gopast */ /* non v, line 60 */
        if (ret < 0) return 0;
        c += ret;
    }
    I_p1 = c; /* setmark p1, line 60 */
    /* try, line 61 */
    if (!(I_p1 < I_x)) goto lab0; /* p1 < <integer expression>, line 61 */
    I_p1 = I_x; /* p1 = <integer expression>, line 61 */
lab0:
    {   int ret = out_grouping_U(g_v, 97, 252, 1); /* gopast */ /* grouping v, line 62 */
        if (ret < 0) return 0;
        c += ret;
    }
    {   int ret = in_grouping_U(g_v, 97, 252, 1); /* gopast */ /* non v, line 62 */
        if (ret < 0) return 0;
        c += ret;
    }
    I_p2 = c; /* setmark p2, line 62 */
    return 1;
}

int Xapian::InternalStemGerman2::r_postlude() { /* forwardmode */
    int among_var;
    while(1) { /* repeat, line 66 */
        int c1 = c;
        bra = c; /* [, line 68 */
        among_var = find_among(s_pool, a_1, 6, 0, 0); /* substring, line 68 */
        if (!(among_var)) goto lab0;
        ket = c; /* ], line 68 */
        switch(among_var) { /* among, line 68 */
            case 0: goto lab0;
            case 1:
                {   int ret = slice_from_s(1, s_6); /* <-, line 69 */
                    if (ret < 0) return ret;
                }
                break;
            case 2:
                {   int ret = slice_from_s(1, s_7); /* <-, line 70 */
                    if (ret < 0) return ret;
                }
                break;
            case 3:
                {   int ret = slice_from_s(1, s_8); /* <-, line 71 */
                    if (ret < 0) return ret;
                }
                break;
            case 4:
                {   int ret = slice_from_s(1, s_9); /* <-, line 72 */
                    if (ret < 0) return ret;
                }
                break;
            case 5:
                {   int ret = slice_from_s(1, s_10); /* <-, line 73 */
                    if (ret < 0) return ret;
                }
                break;
            case 6:
                {   int ret = skip_utf8(p, c, 0, l, 1);
                    if (ret < 0) goto lab0;
                    c = ret; /* next, line 74 */
                }
                break;
        }
        continue;
    lab0:
        c = c1;
        break;
    }
    return 1;
}

int Xapian::InternalStemGerman2::r_R1() { /* backwardmode */
    if (!(I_p1 <= c)) return 0; /* p1 <= <integer expression>, line 81 */
    return 1;
}

int Xapian::InternalStemGerman2::r_R2() { /* backwardmode */
    if (!(I_p2 <= c)) return 0; /* p2 <= <integer expression>, line 82 */
    return 1;
}

int Xapian::InternalStemGerman2::r_standard_suffix() { /* backwardmode */
    int among_var;
    {   int m1 = l - c; (void)m1; /* do, line 85 */
        ket = c; /* [, line 86 */
        if (c <= lb || p[c - 1] >> 5 != 3 || !((811040 >> (p[c - 1] & 0x1f)) & 1)) goto lab0; /* substring, line 86 */
        among_var = find_among_b(s_pool, a_2, 7, 0, 0);
        if (!(among_var)) goto lab0;
        bra = c; /* ], line 86 */
        {   int ret = r_R1(); /* call R1, line 86 */
            if (ret == 0) goto lab0;
            if (ret < 0) return ret;
        }
        switch(among_var) { /* among, line 86 */
            case 0: goto lab0;
            case 1:
                if (slice_del() == -1) return -1; /* delete, line 88 */
                break;
            case 2:
                if (slice_del() == -1) return -1; /* delete, line 91 */
                {   int m2 = l - c; (void)m2; /* try, line 92 */
                    ket = c; /* [, line 92 */
                    if (c <= lb || p[c - 1] != 's') { c = l - m2; goto lab1; }
                    c--;
                    bra = c; /* ], line 92 */
                    if (!(eq_s_b(3, s_11))) { c = l - m2; goto lab1; } /* literal, line 92 */
                    if (slice_del() == -1) return -1; /* delete, line 92 */
                lab1:
                    ;
                }
                break;
            case 3:
                if (in_grouping_b_U(g_s_ending, 98, 116, 0)) goto lab0; /* grouping s_ending, line 95 */
                if (slice_del() == -1) return -1; /* delete, line 95 */
                break;
        }
    lab0:
        c = l - m1;
    }
    {   int m3 = l - c; (void)m3; /* do, line 99 */
        ket = c; /* [, line 100 */
        if (c - 1 <= lb || p[c - 1] >> 5 != 3 || !((1327104 >> (p[c - 1] & 0x1f)) & 1)) goto lab2; /* substring, line 100 */
        among_var = find_among_b(s_pool, a_3, 4, 0, 0);
        if (!(among_var)) goto lab2;
        bra = c; /* ], line 100 */
        {   int ret = r_R1(); /* call R1, line 100 */
            if (ret == 0) goto lab2;
            if (ret < 0) return ret;
        }
        switch(among_var) { /* among, line 100 */
            case 0: goto lab2;
            case 1:
                if (slice_del() == -1) return -1; /* delete, line 102 */
                break;
            case 2:
                if (in_grouping_b_U(g_st_ending, 98, 116, 0)) goto lab2; /* grouping st_ending, line 105 */
                {   int ret = skip_utf8(p, c, lb, l, - 3); /* hop, line 105 */
                    if (ret < 0) goto lab2;
                    c = ret;
                }
                if (slice_del() == -1) return -1; /* delete, line 105 */
                break;
        }
    lab2:
        c = l - m3;
    }
    {   int m4 = l - c; (void)m4; /* do, line 109 */
        ket = c; /* [, line 110 */
        if (c - 1 <= lb || p[c - 1] >> 5 != 3 || !((1051024 >> (p[c - 1] & 0x1f)) & 1)) goto lab3; /* substring, line 110 */
        among_var = find_among_b(s_pool, a_5, 8, 0, 0);
        if (!(among_var)) goto lab3;
        bra = c; /* ], line 110 */
        {   int ret = r_R2(); /* call R2, line 110 */
            if (ret == 0) goto lab3;
            if (ret < 0) return ret;
        }
        switch(among_var) { /* among, line 110 */
            case 0: goto lab3;
            case 1:
                if (slice_del() == -1) return -1; /* delete, line 112 */
                {   int m5 = l - c; (void)m5; /* try, line 113 */
                    ket = c; /* [, line 113 */
                    if (!(eq_s_b(2, s_12))) { c = l - m5; goto lab4; } /* literal, line 113 */
                    bra = c; /* ], line 113 */
                    {   int m6 = l - c; (void)m6; /* not, line 113 */
                        if (c <= lb || p[c - 1] != 'e') goto lab5;
                        c--;
                        { c = l - m5; goto lab4; }
                    lab5:
                        c = l - m6;
                    }
                    {   int ret = r_R2(); /* call R2, line 113 */
                        if (ret == 0) { c = l - m5; goto lab4; }
                        if (ret < 0) return ret;
                    }
                    if (slice_del() == -1) return -1; /* delete, line 113 */
                lab4:
                    ;
                }
                break;
            case 2:
                {   int m7 = l - c; (void)m7; /* not, line 116 */
                    if (c <= lb || p[c - 1] != 'e') goto lab6;
                    c--;
                    goto lab3;
                lab6:
                    c = l - m7;
                }
                if (slice_del() == -1) return -1; /* delete, line 116 */
                break;
            case 3:
                if (slice_del() == -1) return -1; /* delete, line 119 */
                {   int m8 = l - c; (void)m8; /* try, line 120 */
                    ket = c; /* [, line 121 */
                    {   int m9 = l - c; (void)m9; /* or, line 121 */
                        if (!(eq_s_b(2, s_13))) goto lab9; /* literal, line 121 */
                        goto lab8;
                    lab9:
                        c = l - m9;
                        if (!(eq_s_b(2, s_14))) { c = l - m8; goto lab7; } /* literal, line 121 */
                    }
                lab8:
                    bra = c; /* ], line 121 */
                    {   int ret = r_R1(); /* call R1, line 121 */
                        if (ret == 0) { c = l - m8; goto lab7; }
                        if (ret < 0) return ret;
                    }
                    if (slice_del() == -1) return -1; /* delete, line 121 */
                lab7:
                    ;
                }
                break;
            case 4:
                if (slice_del() == -1) return -1; /* delete, line 125 */
                {   int m10 = l - c; (void)m10; /* try, line 126 */
                    ket = c; /* [, line 127 */
                    if (c - 1 <= lb || (p[c - 1] != 103 && p[c - 1] != 104)) { c = l - m10; goto lab10; } /* substring, line 127 */
                    among_var = find_among_b(s_pool, a_4, 2, 0, 0);
                    if (!(among_var)) { c = l - m10; goto lab10; }
                    bra = c; /* ], line 127 */
                    {   int ret = r_R2(); /* call R2, line 127 */
                        if (ret == 0) { c = l - m10; goto lab10; }
                        if (ret < 0) return ret;
                    }
                    switch(among_var) { /* among, line 127 */
                        case 0: { c = l - m10; goto lab10; }
                        case 1:
                            if (slice_del() == -1) return -1; /* delete, line 129 */
                            break;
                    }
                lab10:
                    ;
                }
                break;
        }
    lab3:
        c = l - m4;
    }
    return 1;
}

int Xapian::InternalStemGerman2::stem() { /* forwardmode */
    {   int c1 = c; /* do, line 140 */
        {   int ret = r_prelude(); /* call prelude, line 140 */
            if (ret == 0) goto lab0;
            if (ret < 0) return ret;
        }
    lab0:
        c = c1;
    }
    {   int c2 = c; /* do, line 141 */
        {   int ret = r_mark_regions(); /* call mark_regions, line 141 */
            if (ret == 0) goto lab1;
            if (ret < 0) return ret;
        }
    lab1:
        c = c2;
    }
    lb = c; c = l; /* backwards, line 142 */

    {   int m3 = l - c; (void)m3; /* do, line 143 */
        {   int ret = r_standard_suffix(); /* call standard_suffix, line 143 */
            if (ret == 0) goto lab2;
            if (ret < 0) return ret;
        }
    lab2:
        c = l - m3;
    }
    c = lb;
    {   int c4 = c; /* do, line 144 */
        {   int ret = r_postlude(); /* call postlude, line 144 */
            if (ret == 0) goto lab3;
            if (ret < 0) return ret;
        }
    lab3:
        c = c4;
    }
    return 1;
}

Xapian::InternalStemGerman2::InternalStemGerman2()
    : I_x(0), I_p2(0), I_p1(0)
{
}

Xapian::InternalStemGerman2::~InternalStemGerman2()
{
}

std::string
Xapian::InternalStemGerman2::get_description() const
{
    return "german2";
}
