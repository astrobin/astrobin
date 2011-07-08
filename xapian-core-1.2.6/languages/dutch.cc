/* This file was generated automatically by the Snowball to ISO C++ compiler */

#include <limits.h>
#include "dutch.h"

static const symbol s_pool[] = {
#define s_0_1 0
0xC3, 0xA1,
#define s_0_2 2
0xC3, 0xA4,
#define s_0_3 4
0xC3, 0xA9,
#define s_0_4 6
0xC3, 0xAB,
#define s_0_5 8
0xC3, 0xAD,
#define s_0_6 10
0xC3, 0xAF,
#define s_0_7 12
0xC3, 0xB3,
#define s_0_8 14
0xC3, 0xB6,
#define s_0_9 16
0xC3, 0xBA,
#define s_0_10 18
0xC3, 0xBC,
#define s_1_1 20
'I',
#define s_1_2 21
'Y',
#define s_2_0 22
'd', 'd',
#define s_2_1 24
'k', 'k',
#define s_2_2 26
't', 't',
#define s_3_0 28
'e', 'n', 'e',
#define s_3_1 31
's', 'e',
#define s_3_2 s_3_0
#define s_3_3 33
'h', 'e', 'd', 'e', 'n',
#define s_3_4 s_3_1
#define s_4_0 38
'e', 'n', 'd',
#define s_4_1 41
'i', 'g',
#define s_4_2 43
'i', 'n', 'g',
#define s_4_3 46
'l', 'i', 'j', 'k',
#define s_4_4 50
'b', 'a', 'a', 'r',
#define s_4_5 54
'b', 'a', 'r',
#define s_5_0 57
'a', 'a',
#define s_5_1 59
'e', 'e',
#define s_5_2 61
'o', 'o',
#define s_5_3 63
'u', 'u',
};


static const struct among a_0[11] =
{
/*  0 */ { 0, 0, -1, 6},
/*  1 */ { 2, s_0_1, 0, 1},
/*  2 */ { 2, s_0_2, 0, 1},
/*  3 */ { 2, s_0_3, 0, 2},
/*  4 */ { 2, s_0_4, 0, 2},
/*  5 */ { 2, s_0_5, 0, 3},
/*  6 */ { 2, s_0_6, 0, 3},
/*  7 */ { 2, s_0_7, 0, 4},
/*  8 */ { 2, s_0_8, 0, 4},
/*  9 */ { 2, s_0_9, 0, 5},
/* 10 */ { 2, s_0_10, 0, 5}
};


static const struct among a_1[3] =
{
/*  0 */ { 0, 0, -1, 3},
/*  1 */ { 1, s_1_1, 0, 2},
/*  2 */ { 1, s_1_2, 0, 1}
};


static const struct among a_2[3] =
{
/*  0 */ { 2, s_2_0, -1, -1},
/*  1 */ { 2, s_2_1, -1, -1},
/*  2 */ { 2, s_2_2, -1, -1}
};


static const struct among a_3[5] =
{
/*  0 */ { 3, s_3_0, -1, 2},
/*  1 */ { 2, s_3_1, -1, 3},
/*  2 */ { 2, s_3_2, -1, 2},
/*  3 */ { 5, s_3_3, 2, 1},
/*  4 */ { 1, s_3_4, -1, 3}
};


static const struct among a_4[6] =
{
/*  0 */ { 3, s_4_0, -1, 1},
/*  1 */ { 2, s_4_1, -1, 2},
/*  2 */ { 3, s_4_2, -1, 1},
/*  3 */ { 4, s_4_3, -1, 3},
/*  4 */ { 4, s_4_4, -1, 4},
/*  5 */ { 3, s_4_5, -1, 5}
};


static const struct among a_5[4] =
{
/*  0 */ { 2, s_5_0, -1, -1},
/*  1 */ { 2, s_5_1, -1, -1},
/*  2 */ { 2, s_5_2, -1, -1},
/*  3 */ { 2, s_5_3, -1, -1}
};

static const unsigned char g_v[] = { 17, 65, 16, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 128 };

static const unsigned char g_v_I[] = { 1, 0, 0, 17, 65, 16, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 128 };

static const unsigned char g_v_j[] = { 17, 67, 16, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 128 };

static const symbol s_0[] = { 'a' };
static const symbol s_1[] = { 'e' };
static const symbol s_2[] = { 'i' };
static const symbol s_3[] = { 'o' };
static const symbol s_4[] = { 'u' };
static const symbol s_5[] = { 'Y' };
static const symbol s_6[] = { 'I' };
static const symbol s_7[] = { 'Y' };
static const symbol s_8[] = { 'y' };
static const symbol s_9[] = { 'i' };
static const symbol s_10[] = { 'g', 'e', 'm' };
static const symbol s_11[] = { 'h', 'e', 'i', 'd' };
static const symbol s_12[] = { 'h', 'e', 'i', 'd' };
static const symbol s_13[] = { 'e', 'n' };
static const symbol s_14[] = { 'i', 'g' };

int Xapian::InternalStemDutch::r_prelude() { /* forwardmode */
    int among_var;
    {   int c_test1 = c; /* test, line 42 */
        while(1) { /* repeat, line 42 */
            int c2 = c;
            bra = c; /* [, line 43 */
            if (c + 1 >= l || p[c + 1] >> 5 != 5 || !((340306450 >> (p[c + 1] & 0x1f)) & 1)) among_var = 6; else /* substring, line 43 */
            among_var = find_among(s_pool, a_0, 11, 0, 0);
            if (!(among_var)) goto lab0;
            ket = c; /* ], line 43 */
            switch(among_var) { /* among, line 43 */
                case 0: goto lab0;
                case 1:
                    {   int ret = slice_from_s(1, s_0); /* <-, line 45 */
                        if (ret < 0) return ret;
                    }
                    break;
                case 2:
                    {   int ret = slice_from_s(1, s_1); /* <-, line 47 */
                        if (ret < 0) return ret;
                    }
                    break;
                case 3:
                    {   int ret = slice_from_s(1, s_2); /* <-, line 49 */
                        if (ret < 0) return ret;
                    }
                    break;
                case 4:
                    {   int ret = slice_from_s(1, s_3); /* <-, line 51 */
                        if (ret < 0) return ret;
                    }
                    break;
                case 5:
                    {   int ret = slice_from_s(1, s_4); /* <-, line 53 */
                        if (ret < 0) return ret;
                    }
                    break;
                case 6:
                    {   int ret = skip_utf8(p, c, 0, l, 1);
                        if (ret < 0) goto lab0;
                        c = ret; /* next, line 54 */
                    }
                    break;
            }
            continue;
        lab0:
            c = c2;
            break;
        }
        c = c_test1;
    }
    {   int c3 = c; /* try, line 57 */
        bra = c; /* [, line 57 */
        if (c == l || p[c] != 'y') { c = c3; goto lab1; }
        c++;
        ket = c; /* ], line 57 */
        {   int ret = slice_from_s(1, s_5); /* <-, line 57 */
            if (ret < 0) return ret;
        }
    lab1:
        ;
    }
    while(1) { /* repeat, line 58 */
        int c4 = c;
        while(1) { /* goto, line 58 */
            int c5 = c;
            if (in_grouping_U(g_v, 97, 232, 0)) goto lab3; /* grouping v, line 59 */
            bra = c; /* [, line 59 */
            {   int c6 = c; /* or, line 59 */
                if (c == l || p[c] != 'i') goto lab5;
                c++;
                ket = c; /* ], line 59 */
                if (in_grouping_U(g_v, 97, 232, 0)) goto lab5; /* grouping v, line 59 */
                {   int ret = slice_from_s(1, s_6); /* <-, line 59 */
                    if (ret < 0) return ret;
                }
                goto lab4;
            lab5:
                c = c6;
                if (c == l || p[c] != 'y') goto lab3;
                c++;
                ket = c; /* ], line 60 */
                {   int ret = slice_from_s(1, s_7); /* <-, line 60 */
                    if (ret < 0) return ret;
                }
            }
        lab4:
            c = c5;
            break;
        lab3:
            c = c5;
            {   int ret = skip_utf8(p, c, 0, l, 1);
                if (ret < 0) goto lab2;
                c = ret; /* goto, line 58 */
            }
        }
        continue;
    lab2:
        c = c4;
        break;
    }
    return 1;
}

int Xapian::InternalStemDutch::r_mark_regions() { /* forwardmode */
    I_p1 = l; /* p1 = <integer expression>, line 66 */
    I_p2 = l; /* p2 = <integer expression>, line 67 */
    {   int ret = out_grouping_U(g_v, 97, 232, 1); /* gopast */ /* grouping v, line 69 */
        if (ret < 0) return 0;
        c += ret;
    }
    {   int ret = in_grouping_U(g_v, 97, 232, 1); /* gopast */ /* non v, line 69 */
        if (ret < 0) return 0;
        c += ret;
    }
    I_p1 = c; /* setmark p1, line 69 */
    /* try, line 70 */
    if (!(I_p1 < 3)) goto lab0; /* p1 < <integer expression>, line 70 */
    I_p1 = 3; /* p1 = <integer expression>, line 70 */
lab0:
    {   int ret = out_grouping_U(g_v, 97, 232, 1); /* gopast */ /* grouping v, line 71 */
        if (ret < 0) return 0;
        c += ret;
    }
    {   int ret = in_grouping_U(g_v, 97, 232, 1); /* gopast */ /* non v, line 71 */
        if (ret < 0) return 0;
        c += ret;
    }
    I_p2 = c; /* setmark p2, line 71 */
    return 1;
}

int Xapian::InternalStemDutch::r_postlude() { /* forwardmode */
    int among_var;
    while(1) { /* repeat, line 75 */
        int c1 = c;
        bra = c; /* [, line 77 */
        if (c >= l || (p[c + 0] != 73 && p[c + 0] != 89)) among_var = 3; else /* substring, line 77 */
        among_var = find_among(s_pool, a_1, 3, 0, 0);
        if (!(among_var)) goto lab0;
        ket = c; /* ], line 77 */
        switch(among_var) { /* among, line 77 */
            case 0: goto lab0;
            case 1:
                {   int ret = slice_from_s(1, s_8); /* <-, line 78 */
                    if (ret < 0) return ret;
                }
                break;
            case 2:
                {   int ret = slice_from_s(1, s_9); /* <-, line 79 */
                    if (ret < 0) return ret;
                }
                break;
            case 3:
                {   int ret = skip_utf8(p, c, 0, l, 1);
                    if (ret < 0) goto lab0;
                    c = ret; /* next, line 80 */
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

int Xapian::InternalStemDutch::r_R1() { /* backwardmode */
    if (!(I_p1 <= c)) return 0; /* p1 <= <integer expression>, line 87 */
    return 1;
}

int Xapian::InternalStemDutch::r_R2() { /* backwardmode */
    if (!(I_p2 <= c)) return 0; /* p2 <= <integer expression>, line 88 */
    return 1;
}

int Xapian::InternalStemDutch::r_undouble() { /* backwardmode */
    {   int m_test1 = l - c; /* test, line 91 */
        if (c - 1 <= lb || p[c - 1] >> 5 != 3 || !((1050640 >> (p[c - 1] & 0x1f)) & 1)) return 0; /* among, line 91 */
        if (!(find_among_b(s_pool, a_2, 3, 0, 0))) return 0;
        c = l - m_test1;
    }
    ket = c; /* [, line 91 */
    {   int ret = skip_utf8(p, c, lb, 0, -1);
        if (ret < 0) return 0;
        c = ret; /* next, line 91 */
    }
    bra = c; /* ], line 91 */
    if (slice_del() == -1) return -1; /* delete, line 91 */
    return 1;
}

int Xapian::InternalStemDutch::r_e_ending() { /* backwardmode */
    B_e_found = 0; /* unset e_found, line 95 */
    ket = c; /* [, line 96 */
    if (c <= lb || p[c - 1] != 'e') return 0;
    c--;
    bra = c; /* ], line 96 */
    {   int ret = r_R1(); /* call R1, line 96 */
        if (ret <= 0) return ret;
    }
    {   int m_test1 = l - c; /* test, line 96 */
        if (out_grouping_b_U(g_v, 97, 232, 0)) return 0; /* non v, line 96 */
        c = l - m_test1;
    }
    if (slice_del() == -1) return -1; /* delete, line 96 */
    B_e_found = 1; /* set e_found, line 97 */
    {   int ret = r_undouble(); /* call undouble, line 98 */
        if (ret <= 0) return ret;
    }
    return 1;
}

int Xapian::InternalStemDutch::r_en_ending() { /* backwardmode */
    {   int ret = r_R1(); /* call R1, line 102 */
        if (ret <= 0) return ret;
    }
    {   int m1 = l - c; (void)m1; /* and, line 102 */
        if (out_grouping_b_U(g_v, 97, 232, 0)) return 0; /* non v, line 102 */
        c = l - m1;
        {   int m2 = l - c; (void)m2; /* not, line 102 */
            if (!(eq_s_b(3, s_10))) goto lab0; /* literal, line 102 */
            return 0;
        lab0:
            c = l - m2;
        }
    }
    if (slice_del() == -1) return -1; /* delete, line 102 */
    {   int ret = r_undouble(); /* call undouble, line 103 */
        if (ret <= 0) return ret;
    }
    return 1;
}

int Xapian::InternalStemDutch::r_standard_suffix() { /* backwardmode */
    int among_var;
    {   int m1 = l - c; (void)m1; /* do, line 107 */
        ket = c; /* [, line 108 */
        if (c <= lb || p[c - 1] >> 5 != 3 || !((540704 >> (p[c - 1] & 0x1f)) & 1)) goto lab0; /* substring, line 108 */
        among_var = find_among_b(s_pool, a_3, 5, 0, 0);
        if (!(among_var)) goto lab0;
        bra = c; /* ], line 108 */
        switch(among_var) { /* among, line 108 */
            case 0: goto lab0;
            case 1:
                {   int ret = r_R1(); /* call R1, line 110 */
                    if (ret == 0) goto lab0;
                    if (ret < 0) return ret;
                }
                {   int ret = slice_from_s(4, s_11); /* <-, line 110 */
                    if (ret < 0) return ret;
                }
                break;
            case 2:
                {   int ret = r_en_ending(); /* call en_ending, line 113 */
                    if (ret == 0) goto lab0;
                    if (ret < 0) return ret;
                }
                break;
            case 3:
                {   int ret = r_R1(); /* call R1, line 116 */
                    if (ret == 0) goto lab0;
                    if (ret < 0) return ret;
                }
                if (out_grouping_b_U(g_v_j, 97, 232, 0)) goto lab0; /* non v_j, line 116 */
                if (slice_del() == -1) return -1; /* delete, line 116 */
                break;
        }
    lab0:
        c = l - m1;
    }
    {   int m2 = l - c; (void)m2; /* do, line 120 */
        {   int ret = r_e_ending(); /* call e_ending, line 120 */
            if (ret == 0) goto lab1;
            if (ret < 0) return ret;
        }
    lab1:
        c = l - m2;
    }
    {   int m3 = l - c; (void)m3; /* do, line 122 */
        ket = c; /* [, line 122 */
        if (!(eq_s_b(4, s_12))) goto lab2; /* literal, line 122 */
        bra = c; /* ], line 122 */
        {   int ret = r_R2(); /* call R2, line 122 */
            if (ret == 0) goto lab2;
            if (ret < 0) return ret;
        }
        {   int m4 = l - c; (void)m4; /* not, line 122 */
            if (c <= lb || p[c - 1] != 'c') goto lab3;
            c--;
            goto lab2;
        lab3:
            c = l - m4;
        }
        if (slice_del() == -1) return -1; /* delete, line 122 */
        ket = c; /* [, line 123 */
        if (!(eq_s_b(2, s_13))) goto lab2; /* literal, line 123 */
        bra = c; /* ], line 123 */
        {   int ret = r_en_ending(); /* call en_ending, line 123 */
            if (ret == 0) goto lab2;
            if (ret < 0) return ret;
        }
    lab2:
        c = l - m3;
    }
    {   int m5 = l - c; (void)m5; /* do, line 126 */
        ket = c; /* [, line 127 */
        if (c - 1 <= lb || p[c - 1] >> 5 != 3 || !((264336 >> (p[c - 1] & 0x1f)) & 1)) goto lab4; /* substring, line 127 */
        among_var = find_among_b(s_pool, a_4, 6, 0, 0);
        if (!(among_var)) goto lab4;
        bra = c; /* ], line 127 */
        switch(among_var) { /* among, line 127 */
            case 0: goto lab4;
            case 1:
                {   int ret = r_R2(); /* call R2, line 129 */
                    if (ret == 0) goto lab4;
                    if (ret < 0) return ret;
                }
                if (slice_del() == -1) return -1; /* delete, line 129 */
                {   int m6 = l - c; (void)m6; /* or, line 130 */
                    ket = c; /* [, line 130 */
                    if (!(eq_s_b(2, s_14))) goto lab6; /* literal, line 130 */
                    bra = c; /* ], line 130 */
                    {   int ret = r_R2(); /* call R2, line 130 */
                        if (ret == 0) goto lab6;
                        if (ret < 0) return ret;
                    }
                    {   int m7 = l - c; (void)m7; /* not, line 130 */
                        if (c <= lb || p[c - 1] != 'e') goto lab7;
                        c--;
                        goto lab6;
                    lab7:
                        c = l - m7;
                    }
                    if (slice_del() == -1) return -1; /* delete, line 130 */
                    goto lab5;
                lab6:
                    c = l - m6;
                    {   int ret = r_undouble(); /* call undouble, line 130 */
                        if (ret == 0) goto lab4;
                        if (ret < 0) return ret;
                    }
                }
            lab5:
                break;
            case 2:
                {   int ret = r_R2(); /* call R2, line 133 */
                    if (ret == 0) goto lab4;
                    if (ret < 0) return ret;
                }
                {   int m8 = l - c; (void)m8; /* not, line 133 */
                    if (c <= lb || p[c - 1] != 'e') goto lab8;
                    c--;
                    goto lab4;
                lab8:
                    c = l - m8;
                }
                if (slice_del() == -1) return -1; /* delete, line 133 */
                break;
            case 3:
                {   int ret = r_R2(); /* call R2, line 136 */
                    if (ret == 0) goto lab4;
                    if (ret < 0) return ret;
                }
                if (slice_del() == -1) return -1; /* delete, line 136 */
                {   int ret = r_e_ending(); /* call e_ending, line 136 */
                    if (ret == 0) goto lab4;
                    if (ret < 0) return ret;
                }
                break;
            case 4:
                {   int ret = r_R2(); /* call R2, line 139 */
                    if (ret == 0) goto lab4;
                    if (ret < 0) return ret;
                }
                if (slice_del() == -1) return -1; /* delete, line 139 */
                break;
            case 5:
                {   int ret = r_R2(); /* call R2, line 142 */
                    if (ret == 0) goto lab4;
                    if (ret < 0) return ret;
                }
                if (!(B_e_found)) goto lab4; /* Boolean test e_found, line 142 */
                if (slice_del() == -1) return -1; /* delete, line 142 */
                break;
        }
    lab4:
        c = l - m5;
    }
    {   int m9 = l - c; (void)m9; /* do, line 146 */
        if (out_grouping_b_U(g_v_I, 73, 232, 0)) goto lab9; /* non v_I, line 147 */
        {   int m_test10 = l - c; /* test, line 148 */
            if (c - 1 <= lb || p[c - 1] >> 5 != 3 || !((2129954 >> (p[c - 1] & 0x1f)) & 1)) goto lab9; /* among, line 149 */
            if (!(find_among_b(s_pool, a_5, 4, 0, 0))) goto lab9;
            if (out_grouping_b_U(g_v, 97, 232, 0)) goto lab9; /* non v, line 150 */
            c = l - m_test10;
        }
        ket = c; /* [, line 152 */
        {   int ret = skip_utf8(p, c, lb, 0, -1);
            if (ret < 0) goto lab9;
            c = ret; /* next, line 152 */
        }
        bra = c; /* ], line 152 */
        if (slice_del() == -1) return -1; /* delete, line 152 */
    lab9:
        c = l - m9;
    }
    return 1;
}

int Xapian::InternalStemDutch::stem() { /* forwardmode */
    {   int c1 = c; /* do, line 159 */
        {   int ret = r_prelude(); /* call prelude, line 159 */
            if (ret == 0) goto lab0;
            if (ret < 0) return ret;
        }
    lab0:
        c = c1;
    }
    {   int c2 = c; /* do, line 160 */
        {   int ret = r_mark_regions(); /* call mark_regions, line 160 */
            if (ret == 0) goto lab1;
            if (ret < 0) return ret;
        }
    lab1:
        c = c2;
    }
    lb = c; c = l; /* backwards, line 161 */

    {   int m3 = l - c; (void)m3; /* do, line 162 */
        {   int ret = r_standard_suffix(); /* call standard_suffix, line 162 */
            if (ret == 0) goto lab2;
            if (ret < 0) return ret;
        }
    lab2:
        c = l - m3;
    }
    c = lb;
    {   int c4 = c; /* do, line 163 */
        {   int ret = r_postlude(); /* call postlude, line 163 */
            if (ret == 0) goto lab3;
            if (ret < 0) return ret;
        }
    lab3:
        c = c4;
    }
    return 1;
}

Xapian::InternalStemDutch::InternalStemDutch()
    : I_p2(0), I_p1(0), B_e_found(0)
{
}

Xapian::InternalStemDutch::~InternalStemDutch()
{
}

std::string
Xapian::InternalStemDutch::get_description() const
{
    return "dutch";
}
