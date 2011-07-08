/* Driver template for the LEMON parser generator.
** The author disclaims copyright to this source code.
**
** Synced with upstream CVS rev 1.45:
** http://www.sqlite.org/cvstrac/fileview?f=sqlite/tool/lempar.c&v=1.45
*/
/* First off, code is included that follows the "include" declaration
** in the input grammar file. */
#line 1 "queryparser/queryparser.lemony"

/* queryparser.lemony: build a Xapian::Query object from a user query string.
 *
 * Copyright (C) 2004,2005,2006,2007,2008,2009,2010,2011 Olly Betts
 * Copyright (C) 2007,2008,2009 Lemur Consulting Ltd
 * Copyright (C) 2010 Adam Sjøgren
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301
 * USA
 */

#include <config.h>

#include "omassert.h"
#include "queryparser_internal.h"
#include <xapian/error.h>
#include <xapian/unicode.h>
#include "str.h"
#include "stringutils.h"

// Include the list of token values lemon generates.
#include "queryparser_token.h"

#include <algorithm>
#include <list>
#include <string>

#include <string.h>

using namespace std;

using namespace Xapian;

inline bool
U_isupper(unsigned ch) {
    return (ch < 128 && C_isupper((unsigned char)ch));
}

inline bool
U_isdigit(unsigned ch) {
    return (ch < 128 && C_isdigit((unsigned char)ch));
}

inline bool
U_isalpha(unsigned ch) {
    return (ch < 128 && C_isalpha((unsigned char)ch));
}

using Xapian::Unicode::is_whitespace;

inline bool
is_not_whitespace(unsigned ch) {
    return !is_whitespace(ch);
}

using Xapian::Unicode::is_wordchar;

inline bool
is_not_wordchar(unsigned ch) {
    return !is_wordchar(ch);
}

inline bool
is_digit(unsigned ch) {
    return (Unicode::get_category(ch) == Unicode::DECIMAL_DIGIT_NUMBER);
}

// FIXME: we used to keep trailing "-" (e.g. Cl-) but it's of dubious utility
// and there's the risk of hyphens getting stuck onto the end of terms...
inline bool
is_suffix(unsigned ch) {
    return ch == '+' || ch == '#';
}

inline bool
prefix_needs_colon(const string & prefix, unsigned ch)
{
    if (!U_isupper(ch)) return false;
    string::size_type len = prefix.length();
    return (len > 1 && prefix[len - 1] != ':');
}

using Unicode::is_currency;

inline bool
is_positional(Xapian::Query::op op)
{
    return (op == Xapian::Query::OP_PHRASE || op == Xapian::Query::OP_NEAR);
}

/// A structure identifying a group of filter terms or a value range.
struct filter_group_id {
    /** The prefix info for boolean filter terms.
     *
     *  This is NULL for a value range.
     */
    const PrefixInfo *prefix_info;

    /** The value number for a value range.
     *
     *  This is used for value range terms.
     */
    Xapian::valueno slot;

    /// Make a new filter_group_id for boolean filter terms.
    explicit filter_group_id(const PrefixInfo * prefix_info_)
	: prefix_info(prefix_info_), slot(Xapian::BAD_VALUENO) {}

    /// Make a new filter_group_id for value range terms.
    explicit filter_group_id(Xapian::valueno slot_)
	: prefix_info(NULL), slot(slot_) {}

    /// Ordering needed to allow storage in a map.
    bool operator<(const filter_group_id & other) const {
	// Check slot first since comparison is cheap.
	if (slot != other.slot)
	    return slot < other.slot;
	if (!prefix_info || prefix_info == other.prefix_info)
	    return false;
	if (!other.prefix_info)
	    return true;
	return prefix_info->prefixes < other.prefix_info->prefixes;
    }
};

/** Class used to pass information about a token from lexer to parser.
 *
 *  Generally an instance of this class carries term information, but it can be
 *  used for the start or end of a value range, with some operators (e.g. the
 *  distance in NEAR/3 or ADJ/3, etc).
 */
class Term {
    State * state;

  public:
    string name;
    const PrefixInfo * prefix_info;
    string unstemmed;
    QueryParser::stem_strategy stem;
    termpos pos;

    Term(const string &name_, termpos pos_) : name(name_), stem(QueryParser::STEM_NONE), pos(pos_) { }
    Term(const string &name_) : name(name_), stem(QueryParser::STEM_NONE), pos(0) { }
    Term(const string &name_, const PrefixInfo * prefix_info_)
	: name(name_), prefix_info(prefix_info_),
	  stem(QueryParser::STEM_NONE), pos(0) { }
    Term(termpos pos_) : stem(QueryParser::STEM_NONE), pos(pos_) { }
    Term(State * state_, const string &name_, const PrefixInfo * prefix_info_,
	 const string &unstemmed_,
	 QueryParser::stem_strategy stem_ = QueryParser::STEM_NONE,
	 termpos pos_ = 0)
	: state(state_), name(name_), prefix_info(prefix_info_),
	  unstemmed(unstemmed_), stem(stem_), pos(pos_) { }
    // For RANGE tokens.
    Term(valueno slot, const string &a, const string &b)
	: name(a), unstemmed(b), pos(slot) { }

    string make_term(const string & prefix) const;

    void need_positions() {
	if (stem == QueryParser::STEM_SOME) stem = QueryParser::STEM_NONE;
    }

    termpos get_termpos() const { return pos; }

    filter_group_id get_filter_group_id() const {
	return filter_group_id(prefix_info);
    }

    Query * as_wildcarded_query(State * state) const;

    /** Build a query for a term at the very end of the query string when
     *  FLAG_PARTIAL is in use.
     *
     *  This query should match documents containing any terms which start with
     *  the characters specified, but should give a higher score to exact
     *  matches (since the user might have finished typing - we simply don't
     *  know).
     */
    Query * as_partial_query(State * state_) const;

    /// Value range query.
    Query as_value_range_query() const;

    Query get_query() const;

    Query get_query_with_synonyms() const;

    Query get_query_with_auto_synonyms() const;
};

/// Parser State shared between the lexer and the parser.
class State {
    QueryParser::Internal * qpi;

  public:
    Query query;
    const char * error;
    unsigned flags;

    State(QueryParser::Internal * qpi_, unsigned flags_)
	: qpi(qpi_), error(NULL), flags(flags_) { }

    string stem_term(const string &term) {
	return qpi->stemmer(term);
    }

    void add_to_stoplist(const Term * term) {
	qpi->stoplist.push_back(term->name);
    }

    void add_to_unstem(const string & term, const string & unstemmed) {
	qpi->unstem.insert(make_pair(term, unstemmed));
    }

    Term * value_range(const string &a, const string &b) {
	list<ValueRangeProcessor *>::const_iterator i;
	for (i = qpi->valrangeprocs.begin(); i != qpi->valrangeprocs.end(); ++i) {
	    string start = a;
	    string end = b;
	    Xapian::valueno slot = (**i)(start, end);
	    if (slot != Xapian::BAD_VALUENO) {
		return new Term(slot, start, end);
	    }
	}
	return NULL;
    }

    Query::op default_op() const { return qpi->default_op; }

    bool is_stopword(const Term *term) const {
	return qpi->stopper && (*qpi->stopper)(term->name);
    }

    Database get_database() const {
	return qpi->db;
    }

    const Stopper * get_stopper() const {
	return qpi->stopper;
    }

    size_t stoplist_size() const {
	return qpi->stoplist.size();
    }

    void stoplist_resize(size_t s) {
	qpi->stoplist.resize(s);
    }

    Xapian::termcount get_max_wildcard_expansion() const {
	return qpi->max_wildcard_expansion;
    }
};

string
Term::make_term(const string & prefix) const
{
    string term;
    if (stem == QueryParser::STEM_SOME) term += 'Z';
    if (!prefix.empty()) {
	term += prefix;
	if (prefix_needs_colon(prefix, name[0])) term += ':';
    }
    if (stem != QueryParser::STEM_NONE) {
	term += state->stem_term(name);
    } else {
	term += name;
    }

    if (!unstemmed.empty())
	state->add_to_unstem(term, unstemmed);
    return term;
}

Query
Term::get_query_with_synonyms() const
{
    Query q = get_query();

    // Handle single-word synonyms with each prefix.
    const list<string> & prefixes = prefix_info->prefixes;
    list<string>::const_iterator piter;
    for (piter = prefixes.begin(); piter != prefixes.end(); ++piter) {
	// First try the unstemmed term:
	string term;
	if (!piter->empty()) {
	    term += *piter;
	    if (prefix_needs_colon(*piter, name[0])) term += ':';
	}
	term += name;

	Xapian::Database db = state->get_database();
	Xapian::TermIterator syn = db.synonyms_begin(term);
	Xapian::TermIterator end = db.synonyms_end(term);
	if (syn == end && stem != QueryParser::STEM_NONE) {
	    // If that has no synonyms, try the stemmed form:
	    term = 'Z';
	    if (!piter->empty()) {
		term += *piter;
		if (prefix_needs_colon(*piter, name[0])) term += ':';
	    }
	    term += state->stem_term(name);
	    syn = db.synonyms_begin(term);
	    end = db.synonyms_end(term);
	}
	while (syn != end) {
	    q = Query(Query::OP_SYNONYM, q, Query(*syn, 1, pos));
	    ++syn;
	}
    }
    return q;
}

Query
Term::get_query_with_auto_synonyms() const
{
    if (state->flags & QueryParser::FLAG_AUTO_SYNONYMS)
	return get_query_with_synonyms();

    return get_query();
}

static void
add_to_query(Query *& q, Query::op op, Query * term)
{
    Assert(term);
    if (q) {
	*q = Query(op, *q, *term);
	delete term;
    } else {
	q = term;
    }
}

static void
add_to_query(Query *& q, Query::op op, const Query & term)
{
    if (q) {
	*q = Query(op, *q, term);
    } else {
	q = new Query(term);
    }
}

Query
Term::get_query() const
{
    const list<string> & prefixes = prefix_info->prefixes;
    Assert(prefixes.size() >= 1);
    list<string>::const_iterator piter = prefixes.begin();
    Query q(make_term(*piter), 1, pos);
    while (++piter != prefixes.end()) {
	q = Query(Query::OP_OR, q, Query(make_term(*piter), 1, pos));
    }
    return q;
}

Query *
Term::as_wildcarded_query(State * state_) const
{
    const Database & db = state_->get_database();
    vector<Query> subqs;

    const list<string> & prefixes = prefix_info->prefixes;
    list<string>::const_iterator piter;
    Xapian::termcount expansion_count = 0;
    Xapian::termcount max = state_->get_max_wildcard_expansion();
    for (piter = prefixes.begin(); piter != prefixes.end(); ++piter) {
	string root = *piter;
	root += name;
	TermIterator t = db.allterms_begin(root);
	while (t != db.allterms_end(root)) {
	    if (max != 0 && ++expansion_count > max) {
		string msg("Wildcard ");
		msg += unstemmed;
		msg += "* expands to more than ";
		msg += str(max);
		msg += " terms";
		throw Xapian::QueryParserError(msg);
	    }
	    subqs.push_back(Query(*t, 1, pos));
	    ++t;
	}
    }
    Query * q = new Query(Query::OP_SYNONYM, subqs.begin(), subqs.end());
    delete this;
    return q;
}

Query *
Term::as_partial_query(State * state_) const
{
    const Database & db = state_->get_database();
    vector<Query> subqs_partial; // A synonym of all the partial terms.
    vector<Query> subqs_full; // A synonym of all the full terms.

    const list<string> & prefixes = prefix_info->prefixes;
    list<string>::const_iterator piter;
    for (piter = prefixes.begin(); piter != prefixes.end(); ++piter) {
	string root = *piter;
	root += name;
	TermIterator t = db.allterms_begin(root);
	while (t != db.allterms_end(root)) {
	    subqs_partial.push_back(Query(*t, 1, pos));
	    ++t;
	}
	// Add the term, as it would normally be handled, as an alternative.
	subqs_full.push_back(Query(make_term(*piter), 1, pos));
    }
    Query * q = new Query(Query::OP_OR,
			  Query(Query::OP_SYNONYM,
				subqs_partial.begin(), subqs_partial.end()),
			  Query(Query::OP_SYNONYM,
				subqs_full.begin(), subqs_full.end()));
    delete this;
    return q;
}

Query
Term::as_value_range_query() const
{
    Query q;
    if (unstemmed.empty())
	q = Query(Query::OP_VALUE_GE, pos, name);
    else
	q = Query(Query::OP_VALUE_RANGE, pos, name, unstemmed);
    delete this;
    return q;
}

inline bool
is_phrase_generator(unsigned ch)
{
    // These characters generate a phrase search.
    // Ordered mostly by frequency of calls to this function done when
    // running queryparsertest.
    return (ch && ch < 128 && strchr(".-/:\\@", ch) != NULL);
}

inline bool
is_stem_preventer(unsigned ch)
{
    return (ch && ch < 128 && strchr("(/\\@<>=*[{\"", ch) != NULL);
}

inline bool
should_stem(const string & term)
{
    const unsigned int SHOULD_STEM_MASK =
	(1 << Unicode::LOWERCASE_LETTER) |
	(1 << Unicode::TITLECASE_LETTER) |
	(1 << Unicode::MODIFIER_LETTER) |
	(1 << Unicode::OTHER_LETTER);
    Utf8Iterator u(term);
    return ((SHOULD_STEM_MASK >> Unicode::get_category(*u)) & 1);
}

/** Value representing "ignore this" when returned by check_infix() or
 *  check_infix_digit().
 */
const unsigned UNICODE_IGNORE(-1);

inline unsigned check_infix(unsigned ch) {
    if (ch == '\'' || ch == '&' || ch == 0xb7 || ch == 0x5f4 || ch == 0x2027) {
	// Unicode includes all these except '&' in its word boundary rules,
	// as well as 0x2019 (which we handle below) and ':' (for Swedish
	// apparently, but we ignore this for now as it's problematic in
	// real world cases).
	return ch;
    }
    // 0x2019 is Unicode apostrophe and single closing quote.
    // 0x201b is Unicode single opening quote with the tail rising.
    if (ch == 0x2019 || ch == 0x201b) return '\'';
    if (ch >= 0x200b && (ch <= 0x200d || ch == 0x2060 || ch == 0xfeff))
	return UNICODE_IGNORE;
    return 0;
}

inline unsigned check_infix_digit(unsigned ch) {
    // This list of characters comes from Unicode's word identifying algorithm.
    switch (ch) {
	case ',':
	case '.':
	case ';':
	case 0x037e: // GREEK QUESTION MARK
	case 0x0589: // ARMENIAN FULL STOP
	case 0x060D: // ARABIC DATE SEPARATOR
	case 0x07F8: // NKO COMMA
	case 0x2044: // FRACTION SLASH
	case 0xFE10: // PRESENTATION FORM FOR VERTICAL COMMA
	case 0xFE13: // PRESENTATION FORM FOR VERTICAL COLON
	case 0xFE14: // PRESENTATION FORM FOR VERTICAL SEMICOLON
	    return ch;
    }
    if (ch >= 0x200b && (ch <= 0x200d || ch == 0x2060 || ch == 0xfeff))
	return UNICODE_IGNORE;
    return 0;
}

struct yyParser;

// Prototype the functions lemon generates.
static yyParser *ParseAlloc();
static void ParseFree(yyParser *);
static void Parse(yyParser *, int, Term *, State *);
static void yy_parse_failed(yyParser *);

void
QueryParser::Internal::add_prefix(const string &field, const string &prefix,
				  filter_type type)
{
    map<string, PrefixInfo>::iterator p = prefixmap.find(field);
    if (p == prefixmap.end()) {
	prefixmap.insert(make_pair(field, PrefixInfo(type, prefix)));
    } else {
	// Check that this is the same type of filter as the existing one(s).
	if (p->second.type != type) {
	    throw Xapian::InvalidOperationError("Can't use add_prefix() and add_boolean_prefix() on the same field name, or add_boolean_prefix() with different values of the 'exclusive' parameter");
	}
	p->second.prefixes.push_back(prefix);
   }
}

string
QueryParser::Internal::parse_term(Utf8Iterator &it, const Utf8Iterator &end,
				  bool &was_acronym)
{
    string term;
    // Look for initials separated by '.' (e.g. P.T.O., U.N.C.L.E).
    // Don't worry if there's a trailing '.' or not.
    if (U_isupper(*it)) {
	string t;
	Utf8Iterator p = it;
	do {
	    Unicode::append_utf8(t, *p++);
	} while (p != end && *p == '.' && ++p != end && U_isupper(*p));
	// One letter does not make an acronym!  If we handled a single
	// uppercase letter here, we wouldn't catch M&S below.
	if (t.length() > 1) {
	    // Check there's not a (lower case) letter or digit
	    // immediately after it.
	    // FIXME: should I.B.M..P.T.O be a range search?
	    if (p == end || !is_wordchar(*p)) {
		it = p;
		swap(term, t);
	    }
	}
    }
    was_acronym = !term.empty();

    if (term.empty()) {
	unsigned prevch = *it;
	Unicode::append_utf8(term, prevch);
	while (++it != end) {
	    unsigned ch = *it;
	    if (!is_wordchar(ch)) {
		// Treat a single embedded '&' or "'" or similar as a word
		// character (e.g. AT&T, Fred's).  Also, normalise
		// apostrophes to ASCII apostrophe.
		Utf8Iterator p = it;
		++p;
		if (p == end || !is_wordchar(*p)) break;
		unsigned nextch = *p;
		if (is_digit(prevch) && is_digit(nextch)) {
		    ch = check_infix_digit(ch);
		} else {
		    ch = check_infix(ch);
		}
		if (!ch) break;
		if (ch == UNICODE_IGNORE)
		    continue;
	    }
	    Unicode::append_utf8(term, ch);
	    prevch = ch;
	}
	if (it != end && is_suffix(*it)) {
	    string suff_term = term;
	    Utf8Iterator p = it;
	    // Keep trailing + (e.g. C++, Na+) or # (e.g. C#).
	    do {
		if (suff_term.size() - term.size() == 3) {
		    suff_term.resize(0);
		    break;
		}
		suff_term += *p;
	    } while (is_suffix(*++p));
	    if (!suff_term.empty() && (p == end || !is_wordchar(*p))) {
		// If the suffixed term doesn't exist, check that the
		// non-suffixed term does.  This also takes care of
		// the case when QueryParser::set_database() hasn't
		// been called.
		bool use_suff_term = false;
		string lc = Unicode::tolower(suff_term);
		if (db.term_exists(lc)) {
		    use_suff_term = true;
		} else {
		    lc = Unicode::tolower(term);
		    if (!db.term_exists(lc)) use_suff_term = true;
		}
		if (use_suff_term) {
		    term = suff_term;
		    it = p;
		}
	    }
	}
    }
    return term;
}

class ParserHandler {
    yyParser * parser;

  public:
    explicit ParserHandler(yyParser * parser_) : parser(parser_) { }
    operator yyParser*() { return parser; }
    ~ParserHandler() { ParseFree(parser); }
};

Query
QueryParser::Internal::parse_query(const string &qs, unsigned flags,
				   const string &default_prefix)
{
    // Set value_ranges if we may have to handle value ranges in the query.
    bool value_ranges;
    value_ranges = !valrangeprocs.empty() && (qs.find("..") != string::npos);

    termpos term_pos = 1;
    Utf8Iterator it(qs), end;

    State state(this, flags);

    // To successfully apply more than one spelling correction to a query
    // string, we must keep track of the offset due to previous corrections.
    int correction_offset = 0;
    corrected_query.resize(0);

    // Stack of prefixes, used for phrases and subexpressions.
    list<const PrefixInfo *> prefix_stack;

    // If default_prefix is specified, use it.  Otherwise, use any list
    // that has been set for the empty prefix.
    const PrefixInfo def_pfx(NON_BOOLEAN, default_prefix);
    {
	const PrefixInfo * default_prefix_info = &def_pfx;
	if (default_prefix.empty()) {
	    map<string, PrefixInfo>::const_iterator f = prefixmap.find("");
	    if (f != prefixmap.end()) default_prefix_info = &(f->second);
	}

	// We always have the current prefix on the top of the stack.
	prefix_stack.push_back(default_prefix_info);
    }

    ParserHandler pParser(ParseAlloc());

    unsigned newprev = ' ';
main_lex_loop:
    enum {
	DEFAULT, IN_QUOTES, IN_PREFIXED_QUOTES, IN_PHRASED_TERM, IN_GROUP,
	IN_GROUP2, EXPLICIT_SYNONYM
    } mode = DEFAULT;
    while (it != end && !state.error) {
	bool last_was_operator = false;
	bool last_was_operator_needing_term = false;
	if (mode == EXPLICIT_SYNONYM) mode = DEFAULT;
	if (false) {
just_had_operator:
	    if (it == end) break;
	    mode = DEFAULT;
	    last_was_operator_needing_term = false;
	    last_was_operator = true;
	}
	if (false) {
just_had_operator_needing_term:
	    last_was_operator_needing_term = true;
	    last_was_operator = true;
	}
	if (mode == IN_PHRASED_TERM) mode = DEFAULT;
	if (is_whitespace(*it)) {
	    newprev = ' ';
	    ++it;
	    it = find_if(it, end, is_not_whitespace);
	    if (it == end) break;
	}

	if (value_ranges &&
	    (mode == DEFAULT || mode == IN_GROUP || mode == IN_GROUP2)) {
	    // Scan forward to see if this could be the "start of range"
	    // token.  Sadly this has O(n^2) tendencies, though at least
	    // "n" is the number of words in a query which is likely to
	    // remain fairly small.  FIXME: can we tokenise more elegantly?
	    Utf8Iterator it_initial = it;
	    Utf8Iterator p = it;
	    unsigned ch = 0;
	    while (p != end) {
		if (ch == '.' && *p == '.') {
		    string a;
		    while (it != p) {
			Unicode::append_utf8(a, *it++);
		    }
		    // Trim off the trailing ".".
		    a.resize(a.size() - 1);
		    ++p;
		    // Either end of the range can be empty (for an open-ended
		    // range) but both can't be empty.
		    if (!a.empty() || (p != end && *p > ' ' && *p != ')')) {
			string b;
			// Allow any character except whitespace and ')' in the
			// upper bound.  Or should we be consistent with the
			// lower bound?
			while (p != end && *p > ' ' && *p != ')') {
			    Unicode::append_utf8(b, *p++);
			}
			Term * range = state.value_range(a, b);
			if (!range) {
			    state.error = "Unknown range operation";
			    if (a.find(':', 1) == string::npos) {
				goto done;
			    }
			    // Might be a boolean filter with ".." in.  Leave
			    // state.error in case it isn't.
			    it = it_initial;
			    break;
			}
			Parse(pParser, RANGE, range, &state);
		    }
		    it = p;
		    goto main_lex_loop;
		}
		ch = *p;
		if (!(is_wordchar(ch) || is_currency(ch) ||
		      (ch < 128 && strchr("%,-./:@", ch)))) break;
		++p;
	    }
	}

	if (!is_wordchar(*it)) {
	    unsigned prev = newprev;
	    unsigned ch = *it++;
	    newprev = ch;
	    // Drop out of IN_GROUP mode.
	    if (mode == IN_GROUP || mode == IN_GROUP2)
		mode = DEFAULT;
	    switch (ch) {
	      case '"': // Quoted phrase.
		if (mode == DEFAULT) {
		    // Skip whitespace.
		    it = find_if(it, end, is_not_whitespace);
		    if (it == end) {
			// Ignore an unmatched " at the end of the query to
			// avoid generating an empty pair of QUOTEs which will
			// cause a parse error.
			goto done;
		    }
		    if (*it == '"') {
			// Ignore empty "" (but only if we're not already
			// IN_QUOTES as we don't merge two adjacent quoted
			// phrases!)
			newprev = *it++;
			break;
		    }
		}
		if (flags & QueryParser::FLAG_PHRASE) {
		    Parse(pParser, QUOTE, NULL, &state);
		    if (mode == DEFAULT) {
			mode = IN_QUOTES;
		    } else {
			// Remove the prefix we pushed for this phrase.
			if (mode == IN_PREFIXED_QUOTES)
			    prefix_stack.pop_back();
			mode = DEFAULT;
		    }
		}
		break;

	      case '+': case '-': // Loved or hated term/phrase/subexpression.
		// Ignore + or - at the end of the query string.
		if (it == end) goto done;
		if (prev > ' ' && prev != '(') {
		    // Or if not after whitespace or an open bracket.
		    break;
		}
		if (is_whitespace(*it) || *it == '+' || *it == '-') {
		    // Ignore + or - followed by a space, or further + or -.
		    // Postfix + (such as in C++ and H+) is handled as part of
		    // the term lexing code in parse_term().
		    newprev = *it++;
		    break;
		}
		if (mode == DEFAULT && (flags & FLAG_LOVEHATE)) {
		    int token;
		    if (ch == '+') {
			token = LOVE;
		    } else if (last_was_operator) {
			token = HATE_AFTER_AND;
		    } else {
			token = HATE;
		    }
		    Parse(pParser, token, NULL, &state);
		    goto just_had_operator_needing_term;
		}
		// Need to prevent the term after a LOVE or HATE starting a
		// term group...
		break;

	      case '(': // Bracketed subexpression.
		// Skip whitespace.
		it = find_if(it, end, is_not_whitespace);
		// Ignore ( at the end of the query string.
		if (it == end) goto done;
		if (prev > ' ' && strchr("()+-", prev) == NULL) {
		    // Or if not after whitespace or a bracket or '+' or '-'.
		    break;
		}
		if (*it == ')') {
		    // Ignore empty ().
		    newprev = *it++;
		    break;
		}
		if (mode == DEFAULT && (flags & FLAG_BOOLEAN)) {
		    prefix_stack.push_back(prefix_stack.back());
		    Parse(pParser, BRA, NULL, &state);
		}
		break;

	      case ')': // End of bracketed subexpression.
		if (mode == DEFAULT && (flags & FLAG_BOOLEAN)) {
		    // Remove the prefix we pushed for the corresponding BRA.
		    // If brackets are unmatched, it's a syntax error, but
		    // that's no excuse to SEGV!
		    if (prefix_stack.size() > 1) prefix_stack.pop_back();
		    Parse(pParser, KET, NULL, &state);
		}
		break;

	      case '~': // Synonym expansion.
		// Ignore at the end of the query string.
		if (it == end) goto done;
		if (mode == DEFAULT && (flags & FLAG_SYNONYM)) {
		    if (prev > ' ' && strchr("+-(", prev) == NULL) {
			// Or if not after whitespace, +, -, or an open bracket.
			break;
		    }
		    if (!is_wordchar(*it)) {
			// Ignore if not followed by a word character.
			break;
		    }
		    Parse(pParser, SYNONYM, NULL, &state);
		    mode = EXPLICIT_SYNONYM;
		    goto just_had_operator_needing_term;
		}
		break;
	    }
	    // Skip any other characters.
	    continue;
	}

	Assert(is_wordchar(*it));

	size_t term_start_index = it.raw() - qs.data();

	newprev = 'A'; // Any letter will do...

	// A term, a prefix, or a boolean operator.
	const PrefixInfo * prefix_info = NULL;
	if ((mode == DEFAULT || mode == IN_GROUP || mode == IN_GROUP2 || mode == EXPLICIT_SYNONYM) &&
	    !prefixmap.empty()) {
	    // Check for a fieldname prefix (e.g. title:historical).
	    Utf8Iterator p = find_if(it, end, is_not_wordchar);
	    if (p != end && *p == ':' && ++p != end && *p > ' ' && *p != ')') {
		string field;
		p = it;
		while (*p != ':')
		    Unicode::append_utf8(field, *p++);
		map<string, PrefixInfo>::const_iterator f;
		f = prefixmap.find(field);
		if (f != prefixmap.end()) {
		    // Special handling for prefixed fields, depending on the
		    // type of the prefix.
		    unsigned ch = *++p;
		    prefix_info = &(f->second);

		    if (prefix_info->type != NON_BOOLEAN) {
			// Drop out of IN_GROUP if we're in it.
			if (mode == IN_GROUP || mode == IN_GROUP2)
			    mode = DEFAULT;
			it = p;
			string name;
			if (it != end && *it == '"') {
			    // Quoted boolean term (can contain any character).
			    ++it;
			    while (it != end) {
				if (*it == '"') {
				    // Interpret "" as an escaped ".
				    if (++it == end || *it != '"')
					break;
				}
				Unicode::append_utf8(name, *it++);
			    }
			} else {
			    // Can't boolean filter prefix a subexpression, so
			    // just use anything following the prefix until the
			    // next space or ')' as part of the boolean filter
			    // term.
			    while (it != end && *it > ' ' && *it != ')')
				Unicode::append_utf8(name, *it++);
			}
			// Build the unstemmed form in field.
			field += ':';
			field += name;
			// Clear any pending value range error.
			state.error = NULL;
			Term * token = new Term(&state, name, prefix_info, field);
			Parse(pParser, BOOLEAN_FILTER, token, &state);
			continue;
		    }

		    if (ch == '"' && (flags & FLAG_PHRASE)) {
			// Prefixed phrase, e.g.: subject:"space flight"
			mode = IN_PREFIXED_QUOTES;
			Parse(pParser, QUOTE, NULL, &state);
			it = p;
			newprev = ch;
			++it;
			prefix_stack.push_back(prefix_info);
			continue;
		    }

		    if (ch == '(' && (flags & FLAG_BOOLEAN)) {
			// Prefixed subexpression, e.g.: title:(fast NEAR food)
			mode = DEFAULT;
			Parse(pParser, BRA, NULL, &state);
			it = p;
			newprev = ch;
			++it;
			prefix_stack.push_back(prefix_info);
			continue;
		    }

		    if (ch != ':') {
			// Allow 'path:/usr/local' but not 'foo::bar::baz'.
			while (is_phrase_generator(ch)) {
			    if (++p == end)
				goto not_prefix;
			    ch = *p;
			}
		    }

		    if (is_wordchar(ch)) {
			// Prefixed term.
			it = p;
		    } else {
not_prefix:
			// It looks like a prefix but isn't, so parse it as
			// text instead.
			prefix_info = NULL;
		    }
		}
	    }
	}

phrased_term:
	bool was_acronym;
	string term = parse_term(it, end, was_acronym);

	// Boolean operators.
	if ((mode == DEFAULT || mode == IN_GROUP || mode == IN_GROUP2) &&
	    (flags & FLAG_BOOLEAN) &&
	    // Don't want to interpret A.N.D. as an AND operator.
	    !was_acronym &&
	    !prefix_info &&
	    term.size() >= 2 && term.size() <= 4 && U_isalpha(term[0])) {

	    string op = term;
	    if (flags & FLAG_BOOLEAN_ANY_CASE) {
		for (string::iterator i = op.begin(); i != op.end(); ++i) {
		    *i = C_toupper(*i);
		}
	    }
	    if (op.size() == 3) {
		if (op == "AND") {
		    Parse(pParser, AND, NULL, &state);
		    goto just_had_operator;
		}
		if (op == "NOT") {
		    Parse(pParser, NOT, NULL, &state);
		    goto just_had_operator;
		}
		if (op == "XOR") {
		    Parse(pParser, XOR, NULL, &state);
		    goto just_had_operator;
		}
		if (op == "ADJ") {
		    if (it != end && *it == '/') {
			size_t width = 0;
			Utf8Iterator p = it;
			while (++p != end && U_isdigit(*p)) {
			    width = (width * 10) + (*p - '0');
			}
			if (width && (p == end || is_whitespace(*p))) {
			    it = p;
			    Parse(pParser, ADJ, new Term(width), &state);
			    goto just_had_operator;
			}
		    } else {
			Parse(pParser, ADJ, NULL, &state);
			goto just_had_operator;
		    }
		}
	    } else if (op.size() == 2) {
		if (op == "OR") {
		    Parse(pParser, OR, NULL, &state);
		    goto just_had_operator;
		}
	    } else if (op.size() == 4) {
		if (op == "NEAR") {
		    if (it != end && *it == '/') {
			size_t width = 0;
			Utf8Iterator p = it;
			while (++p != end && U_isdigit(*p)) {
			    width = (width * 10) + (*p - '0');
			}
			if (width && (p == end || is_whitespace(*p))) {
			    it = p;
			    Parse(pParser, NEAR, new Term(width), &state);
			    goto just_had_operator;
			}
		    } else {
			Parse(pParser, NEAR, NULL, &state);
			goto just_had_operator;
		    }
		}
	    }
	}

	// If no prefix is set, use the default one.
	if (!prefix_info) prefix_info = prefix_stack.back();

	Assert(prefix_info->type == NON_BOOLEAN);

	{
	    string unstemmed_term(term);
	    term = Unicode::tolower(term);

	    // Reuse stem_strategy - STEM_SOME here means "stem terms except
	    // when used with positional operators".
	    stem_strategy stem_term = stem_action;
	    if (stem_term != STEM_NONE) {
		if (!stemmer.internal.get()) {
		    // No stemmer is set.
		    stem_term = STEM_NONE;
		} else if (stem_term == STEM_SOME) {
		    if (!should_stem(unstemmed_term) ||
			(it != end && is_stem_preventer(*it))) {
			// Don't stem this particular term.
			stem_term = STEM_NONE;
		    }
		}
	    }

	    Term * term_obj = new Term(&state, term, prefix_info,
				       unstemmed_term, stem_term, term_pos++);

	    if (mode == DEFAULT || mode == IN_GROUP || mode == IN_GROUP2) {
		if (it != end) {
		    if ((flags & FLAG_WILDCARD) && *it == '*') {
			Utf8Iterator p(it);
			++p;
			if (p == end || !is_wordchar(*p)) {
			    it = p;
			    if (mode == IN_GROUP || mode == IN_GROUP2) {
				// Drop out of IN_GROUP and flag that the group
				// can be empty if all members are stopwords.
				if (mode == IN_GROUP2)
				    Parse(pParser, EMPTY_GROUP_OK, NULL, &state);
				mode = DEFAULT;
			    }
			    // Wildcard at end of term (also known as
			    // "right truncation").
			    Parse(pParser, WILD_TERM, term_obj, &state);
			    continue;
			}
		    }
		} else {
		    if (flags & FLAG_PARTIAL) {
			if (mode == IN_GROUP || mode == IN_GROUP2) {
			    // Drop out of IN_GROUP and flag that the group
			    // can be empty if all members are stopwords.
			    if (mode == IN_GROUP2)
				Parse(pParser, EMPTY_GROUP_OK, NULL, &state);
			    mode = DEFAULT;
			}
			// Final term of a partial match query, with no
			// following characters - treat as a wildcard.
			Parse(pParser, PARTIAL_TERM, term_obj, &state);
			continue;
		    }
		}
	    }

	    // Check spelling, if we're a normal term, and any of the prefixes
	    // are empty.
	    if ((flags & FLAG_SPELLING_CORRECTION) && !was_acronym) {
		const list<string> & pfxes = prefix_info->prefixes;
		list<string>::const_iterator pfx_it;
		for (pfx_it = pfxes.begin(); pfx_it != pfxes.end(); ++pfx_it) {
		    if (!pfx_it->empty())
			continue;
		    const string & suggest = db.get_spelling_suggestion(term);
		    if (!suggest.empty()) {
			if (corrected_query.empty()) corrected_query = qs;
			size_t term_end_index = it.raw() - qs.data();
			size_t n = term_end_index - term_start_index;
			size_t pos = term_start_index + correction_offset;
			corrected_query.replace(pos, n, suggest);
			correction_offset += suggest.size();
			correction_offset -= n;
		    }
		    break;
		}
	    }

	    if (mode == IN_PHRASED_TERM) {
		Parse(pParser, PHR_TERM, term_obj, &state);
	    } else {
		// See if the next token will be PHR_TERM - if so, this one
		// needs to be TERM not GROUP_TERM.
		if ((mode == IN_GROUP || mode == IN_GROUP2) &&
		    is_phrase_generator(*it)) {
		    // FIXME: can we clean this up?
		    Utf8Iterator p = it;
		    do {
			++p;
		    } while (p != end && is_phrase_generator(*p));
		    // Don't generate a phrase unless the phrase generators are
		    // immediately followed by another term.
		    if (p != end && is_wordchar(*p)) {
			mode = DEFAULT;
		    }
		}

		int token = TERM;
		if (mode == IN_GROUP || mode == IN_GROUP2) {
		    mode = IN_GROUP2;
		    token = GROUP_TERM;
		}
		Parse(pParser, token, term_obj, &state);
		if (token == TERM && mode != DEFAULT)
		    continue;
	    }
	}

	if (it == end) break;

	if (is_phrase_generator(*it)) {
	    // Skip multiple phrase generators.
	    do {
		++it;
	    } while (it != end && is_phrase_generator(*it));
	    // Don't generate a phrase unless the phrase generators are
	    // immediately followed by another term.
	    if (it != end && is_wordchar(*it)) {
		mode = IN_PHRASED_TERM;
		term_start_index = it.raw() - qs.data();
		goto phrased_term;
	    }
	} else if (mode == DEFAULT || mode == IN_GROUP || mode == IN_GROUP2) {
	    int old_mode = mode;
	    mode = DEFAULT;
	    if (!last_was_operator_needing_term && is_whitespace(*it)) {
		newprev = ' ';
		// Skip multiple whitespace.
		do {
		    ++it;
		} while (it != end && is_whitespace(*it));
		// Don't generate a group unless the terms are only separated
		// by whitespace.
		if (it != end && is_wordchar(*it)) {
		    if (old_mode == IN_GROUP || old_mode == IN_GROUP2) {
			mode = IN_GROUP2;
		    } else {
			mode = IN_GROUP;
		    }
		}
	    }
	}
    }
done:
    if (!state.error) {
	// Implicitly close any unclosed quotes...
	if (mode == IN_QUOTES || mode == IN_PREFIXED_QUOTES)
	    Parse(pParser, QUOTE, NULL, &state);
	Parse(pParser, 0, NULL, &state);
    }

    errmsg = state.error;
    return state.query;
}

struct ProbQuery {
    Query * query;
    Query * love;
    Query * hate;
    // filter is a map from prefix to a query for that prefix.  Queries with
    // the same prefix are combined with OR, and the results of this are
    // combined with AND to get the full filter.
    map<filter_group_id, Query> filter;

    ProbQuery() : query(0), love(0), hate(0) { }
    ~ProbQuery() {
	delete query;
	delete love;
	delete hate;
    }

    void add_filter(const filter_group_id & id, const Query & q) {
	filter[id] = q;
    }

    void append_filter(const filter_group_id & id, const Query & qnew) {
	Query & q = filter[id];
	// We OR filters with the same prefix if they're exclusive, otherwise
	// we AND them.
	bool exclusive = (id.prefix_info->type == BOOLEAN_EXCLUSIVE);
	Query::op op = exclusive ? Query::OP_OR : Query::OP_AND;
	q = Query(op, q, qnew);
    }

    void add_filter_range(Xapian::valueno slot, const Query & range) {
	filter[filter_group_id(slot)] = range;
    }

    void append_filter_range(Xapian::valueno slot, const Query & range) {
	Query & q = filter[filter_group_id(slot)];
	q = Query(Query::OP_OR, q, range);
    }

    Query merge_filters() const {
	map<filter_group_id, Query>::const_iterator i = filter.begin();
	Assert(i != filter.end());
	Query q = i->second;
	while (++i != filter.end()) {
	    q = Query(Query::OP_AND, q, i->second);
	}
	return q;
    }
};

/// A group of terms separated only by whitespace.
class TermGroup {
    vector<Term *> terms;

    /** Controls how to handle a group where all terms are stopwords.
     *
     *  If true, then as_group() returns NULL.  If false, then the
     *  stopword status of the terms is ignored.
     */
    bool empty_ok;

  public:
    TermGroup() : empty_ok(false) { }

    /// Add a Term object to this TermGroup object.
    void add_term(Term * term) {
	terms.push_back(term);
    }

    /// Set the empty_ok flag.
    void set_empty_ok() { empty_ok = true; }

    /// Convert to a Xapian::Query * using default_op.
    Query * as_group(State *state) const;

    /** Provide a way to explicitly delete an object of this class.  The
     *  destructor is protected to prevent auto-variables of this type.
     */
    void destroy() { delete this; }

  protected:
    /** Protected destructor, so an auto-variable of this type is a
     *  compile-time error - you must allocate this object with new.
     */
    ~TermGroup() {
	vector<Term*>::const_iterator i;
	for (i = terms.begin(); i != terms.end(); ++i) {
	    delete *i;
	}
    }
};

Query *
TermGroup::as_group(State *state) const
{
    const Xapian::Stopper * stopper = state->get_stopper();
    size_t stoplist_size = state->stoplist_size();
    bool default_op_is_positional = is_positional(state->default_op());
reprocess:
    Query::op default_op = state->default_op();
    vector<Query> subqs;
    subqs.reserve(terms.size());
    if (state->flags & QueryParser::FLAG_AUTO_MULTIWORD_SYNONYMS) {
	// Check for multi-word synonyms.
	Database db = state->get_database();

	string key;
	vector<Term*>::const_iterator begin = terms.begin();
	vector<Term*>::const_iterator i = begin;
	while (i != terms.end()) {
	    TermIterator synkey(db.synonym_keys_begin((*i)->name));
	    TermIterator synend(db.synonym_keys_end((*i)->name));
	    if (synkey == synend) {
		// No multi-synonym matches.
		if (stopper && (*stopper)((*i)->name)) {
		    state->add_to_stoplist(*i);
		} else {
		    if (default_op_is_positional)
			(*i)->need_positions();
		    subqs.push_back((*i)->get_query_with_auto_synonyms());
		}
		begin = ++i;
		continue;
	    }
	    key.resize(0);
	    while (i != terms.end()) {
		if (!key.empty()) key += ' ';
		key += (*i)->name;
		++i;
		synkey.skip_to(key);
		if (synkey == synend || !startswith(*synkey, key)) break;
	    }
	    // Greedily try to match as many consecutive words as possible.
	    TermIterator syn, end;
	    while (true) {
		syn = db.synonyms_begin(key);
		end = db.synonyms_end(key);
		if (syn != end) break;
		if (--i == begin) break;
		key.resize(key.size() - (*i)->name.size() - 1);
	    }
	    if (i == begin) {
		// No multi-synonym matches.
		if (stopper && (*stopper)((*i)->name)) {
		    state->add_to_stoplist(*i);
		} else {
		    if (default_op_is_positional)
			(*i)->need_positions();
		    subqs.push_back((*i)->get_query_with_auto_synonyms());
		}
		begin = ++i;
		continue;
	    }

	    vector<Query> subqs2;
	    vector<Term*>::const_iterator j;
	    for (j = begin; j != i; ++j) {
		if (stopper && (*stopper)((*j)->name)) {
		    state->add_to_stoplist(*j);
		} else {
		    if (default_op_is_positional)
			(*i)->need_positions();
		    subqs2.push_back((*j)->get_query());
		}
	    }
	    Query q_original_terms;
	    if (default_op_is_positional) {
		q_original_terms = Query(default_op,
					 subqs2.begin(), subqs2.end(),
					 subqs2.size() + 9);
	    } else {
		q_original_terms = Query(default_op,
					 subqs2.begin(), subqs2.end());
	    }
	    subqs2.clear();

	    // Use the position of the first term for the synonyms.
	    Xapian::termpos pos = (*begin)->pos;
	    begin = i;
	    while (syn != end) {
		subqs2.push_back(Query(*syn, 1, pos));
		++syn;
	    }
	    Query q_synonym_terms(Query::OP_SYNONYM, subqs2.begin(), subqs2.end());
	    subqs2.clear();
	    subqs.push_back(Query(Query::OP_SYNONYM,
				  q_original_terms, q_synonym_terms));
	}
    } else {
	vector<Term*>::const_iterator i;
	for (i = terms.begin(); i != terms.end(); ++i) {
	    if (stopper && (*stopper)((*i)->name)) {
		state->add_to_stoplist(*i);
	    } else {
		if (default_op_is_positional)
		    (*i)->need_positions();
		subqs.push_back((*i)->get_query_with_auto_synonyms());
	    }
	}
    }

    if (!empty_ok && stopper && subqs.empty() &&
	stoplist_size < state->stoplist_size()) {
	// This group is all stopwords, so roll-back, disable stopper
	// temporarily, and reprocess this group.
	state->stoplist_resize(stoplist_size);
	stopper = NULL;
	goto reprocess;
    }

    Query * q = NULL;
    if (!subqs.empty()) {
	if (default_op_is_positional) {
	    q = new Query(default_op, subqs.begin(), subqs.end(),
			     subqs.size() + 9);
	} else {
	    q = new Query(default_op, subqs.begin(), subqs.end());
	}
    }
    delete this;
    return q;
}

/// Some terms which form a positional sub-query.
class Terms {
    vector<Term *> terms;
    size_t window;

    /** Keep track of whether the terms added all have the same list of
     *  prefixes.  If so, we'll build a set of phrases, one using each prefix.
     *  This works around the limitation that a phrase cannot have multiple
     *  components which are "OR" combinations of terms, but is also probably
     *  what users expect: i.e., if a user specifies a phrase in a field, and
     *  that field maps to multiple prefixes, the user probably wants a phrase
     *  returned with all terms having one of those prefixes, rather than a
     *  phrase comprised of terms with differing prefixes.
     */
    bool uniform_prefixes;

    /** The list of prefixes of the terms added.
     *  This will be NULL if the terms have different prefixes.
     */
    const list<string> * prefixes;

    /// Convert to a query using the given operator and window size.
    Query * as_opwindow_query(Query::op op, Xapian::termcount w_delta) const {
	Query * q = NULL;
	size_t n_terms = terms.size();
	Xapian::termcount w = w_delta + terms.size();
	if (uniform_prefixes) {
	    if (prefixes) {
		list<string>::const_iterator piter;
		for (piter = prefixes->begin(); piter != prefixes->end(); ++piter) {
		    vector<Query> subqs;
		    subqs.reserve(n_terms);
		    vector<Term *>::const_iterator titer;
		    for (titer = terms.begin(); titer != terms.end(); ++titer) {
			Term * t = *titer;
			subqs.push_back(Query(t->make_term(*piter), 1, t->pos));
		    }
		    add_to_query(q, Query::OP_OR,
				 Query(op, subqs.begin(), subqs.end(), w));
		}
	    }
	} else {
	    vector<Query> subqs;
	    subqs.reserve(n_terms);
	    vector<Term *>::const_iterator titer;
	    for (titer = terms.begin(); titer != terms.end(); ++titer) {
		subqs.push_back((*titer)->get_query());
	    }
	    q = new Query(op, subqs.begin(), subqs.end(), w);
	}

	delete this;
	return q;
    }

  public:
    Terms() : window(0), uniform_prefixes(true), prefixes(NULL) { }

    /// Add an unstemmed Term object to this Terms object.
    void add_positional_term(Term * term) {
	const list<string> & term_prefixes = term->prefix_info->prefixes;
	if (terms.empty()) {
	    prefixes = &term_prefixes;
	} else if (uniform_prefixes && prefixes != &term_prefixes) {
	    if (*prefixes != term_prefixes)  {
		prefixes = NULL;
		uniform_prefixes = false;
	    }
	}
	term->need_positions();
	terms.push_back(term);
    }

    void adjust_window(size_t alternative_window) {
	if (alternative_window > window) window = alternative_window;
    }

    /// Convert to a Xapian::Query * using adjacent OP_PHRASE.
    Query * as_phrase_query() const {
	return as_opwindow_query(Query::OP_PHRASE, 0);
    }

    /// Convert to a Xapian::Query * using OP_NEAR.
    Query * as_near_query() const {
	// The common meaning of 'a NEAR b' is "a within 10 terms of b", which
	// means a window size of 11.  For more than 2 terms, we just add one
	// to the window size for each extra term.
	size_t w = window;
	if (w == 0) w = 10;
	return as_opwindow_query(Query::OP_NEAR, w - 1);
    }

    /// Convert to a Xapian::Query * using OP_PHRASE to implement ADJ.
    Query * as_adj_query() const {
	// The common meaning of 'a ADJ b' is "a at most 10 terms before b",
	// which means a window size of 11.  For more than 2 terms, we just add
	// one to the window size for each extra term.
	size_t w = window;
	if (w == 0) w = 10;
	return as_opwindow_query(Query::OP_PHRASE, w - 1);
    }

    /** Provide a way to explicitly delete an object of this class.  The
     *  destructor is protected to prevent auto-variables of this type.
     */
    void destroy() { delete this; }

  protected:
    /** Protected destructor, so an auto-variable of this type is a
     *  compile-time error - you must allocate this object with new.
     */
    ~Terms() {
	vector<Term *>::const_iterator t;
	for (t = terms.begin(); t != terms.end(); ++t) {
	    delete *t;
	}
    }
};

// Helper macro for converting a boolean operation into a Xapian::Query.
#define BOOL_OP_TO_QUERY(E, A, OP, B, OP_TXT) \
    do {\
	if (!A || !B) {\
	    state->error = "Syntax: <expression> "OP_TXT" <expression>";\
	    yy_parse_failed(yypParser);\
	    return;\
	}\
	E = new Query(OP, *A, *B);\
	delete A;\
	delete B;\
    } while (0)

#line 1577 "queryparser/queryparser_internal.cc"
/* Next is all token values, in a form suitable for use by makeheaders.
** This section will be null unless lemon is run with the -m switch.
*/
/* 
** These constants (all generated automatically by the parser generator)
** specify the various kinds of tokens (terminals) that the parser
** understands. 
**
** Each symbol here is a terminal symbol in the grammar.
*/
/* Make sure the INTERFACE macro is defined.
*/
#ifndef INTERFACE
# define INTERFACE 1
#endif
/* The next thing included is series of defines which control
** various aspects of the generated parser.
**    YYCODETYPE         is the data type used for storing terminal
**                       and nonterminal numbers.  "unsigned char" is
**                       used if there are fewer than 250 terminals
**                       and nonterminals.  "int" is used otherwise.
**    YYNOCODE           is a number of type YYCODETYPE which corresponds
**                       to no legal terminal or nonterminal number.  This
**                       number is used to fill in empty slots of the hash 
**                       table.
**    YYFALLBACK         If defined, this indicates that one or more tokens
**                       have fall-back values which should be used if the
**                       original value of the token will not parse.
**    YYACTIONTYPE       is the data type used for storing terminal
**                       and nonterminal numbers.  "unsigned char" is
**                       used if there are fewer than 250 rules and
**                       states combined.  "int" is used otherwise.
**    ParseTOKENTYPE     is the data type used for minor tokens given 
**                       directly to the parser from the tokenizer.
**    YYMINORTYPE        is the data type used for all minor tokens.
**                       This is typically a union of many types, one of
**                       which is ParseTOKENTYPE.  The entry in the union
**                       for base tokens is called "yy0".
**    YYSTACKDEPTH       is the maximum depth of the parser's stack.  If
**                       zero the stack is dynamically sized using realloc()
**    ParseARG_SDECL     A static variable declaration for the %extra_argument
**    ParseARG_PDECL     A parameter declaration for the %extra_argument
**    ParseARG_STORE     Code to store %extra_argument into yypParser
**    ParseARG_FETCH     Code to extract %extra_argument from yypParser
**    YYNSTATE           the combined number of states.
**    YYNRULE            the number of rules in the grammar
**    YYERRORSYMBOL      is the code number of the error symbol.  If not
**                       defined, then do no error processing.
*/
#define YYCODETYPE unsigned char
#define YYNOCODE 39
#define YYACTIONTYPE unsigned char
#define ParseTOKENTYPE Term *
typedef union {
  int yyinit;
  ParseTOKENTYPE yy0;
  int yy8;
  ProbQuery * yy12;
  Terms * yy46;
  Query * yy73;
  TermGroup * yy76;
} YYMINORTYPE;
#ifndef YYSTACKDEPTH
#define YYSTACKDEPTH 100
#endif
#define ParseARG_SDECL State * state;
#define ParseARG_PDECL ,State * state
#define ParseARG_FETCH State * state = yypParser->state
#define ParseARG_STORE yypParser->state = state
#define YYNSTATE 74
#define YYNRULE 53
#define YY_NO_ACTION      (YYNSTATE+YYNRULE+2)
#define YY_ACCEPT_ACTION  (YYNSTATE+YYNRULE+1)
#define YY_ERROR_ACTION   (YYNSTATE+YYNRULE)

/* Define the yytestcase() macro to be a no-op if is not already defined
** otherwise.
**
** Applications can choose to define yytestcase() in the %include section
** to a macro that can assist in verifying code coverage.  For production
** code the yytestcase() macro should be turned off.  But it is useful
** for testing.
*/
#ifndef yytestcase
# define yytestcase(X)
#endif

/* Next are the tables used to determine what action to take based on the
** current state and lookahead token.  These tables are used to implement
** functions that take a state number and lookahead value and return an
** action integer.  
**
** Suppose the action integer is N.  Then the action is determined as
** follows
**
**   0 <= N < YYNSTATE                  Shift N.  That is, push the lookahead
**                                      token onto the stack and goto state N.
**
**   YYNSTATE <= N < YYNSTATE+YYNRULE   Reduce by rule N-YYNSTATE.
**
**   N == YYNSTATE+YYNRULE              A syntax error has occurred.
**
**   N == YYNSTATE+YYNRULE+1            The parser accepts its input.
**
**   N == YYNSTATE+YYNRULE+2            No such action.  Denotes unused
**                                      slots in the yy_action[] table.
**
** The action table is constructed as a single large table named yy_action[].
** Given state S and lookahead X, the action is computed as
**
**      yy_action[ yy_shift_ofst[S] + X ]
**
** If the index value yy_shift_ofst[S]+X is out of range or if the value
** yy_lookahead[yy_shift_ofst[S]+X] is not equal to X or if yy_shift_ofst[S]
** is equal to YY_SHIFT_USE_DFLT, it means that the action is not in the table
** and that yy_default[S] should be used instead.  
**
** The formula above is for computing the action when the lookahead is
** a terminal symbol.  If the lookahead is a non-terminal (as occurs after
** a reduce action) then the yy_reduce_ofst[] array is used in place of
** the yy_shift_ofst[] array and YY_REDUCE_USE_DFLT is used in place of
** YY_SHIFT_USE_DFLT.
**
** The following are the tables generated in this section:
**
**  yy_action[]        A single table containing all actions.
**  yy_lookahead[]     A table containing the lookahead for each entry in
**                     yy_action.  Used to detect hash collisions.
**  yy_shift_ofst[]    For each state, the offset into yy_action for
**                     shifting terminals.
**  yy_reduce_ofst[]   For each state, the offset into yy_action for
**                     shifting non-terminals after a reduce.
**  yy_default[]       Default action for each state.
*/
static const YYACTIONTYPE yy_action[] = {
 /*     0 */   128,   25,   35,   17,    8,   56,   19,   13,   16,   49,
 /*    10 */    28,   24,   29,   31,    6,    1,    2,   11,   12,    7,
 /*    20 */    34,   15,   23,   74,   45,   46,   71,   57,   14,    5,
 /*    30 */    38,   35,   36,    8,   56,   19,   13,   16,   42,   28,
 /*    40 */    24,   29,   31,   38,   35,   37,    8,   56,   19,   13,
 /*    50 */    16,   43,   28,   24,   29,   31,   38,   35,   21,    8,
 /*    60 */    56,   19,   13,   16,   50,   28,   24,   29,   31,   38,
 /*    70 */    35,   22,    8,   56,   19,   13,   16,   30,   28,   24,
 /*    80 */    29,   31,   33,   35,   17,    8,   56,   19,   13,   16,
 /*    90 */    53,   28,   24,   29,   31,   38,   35,   72,    8,   56,
 /*   100 */    19,   13,   16,   32,   28,   24,   29,   31,   38,   35,
 /*   110 */    73,    8,   56,   19,   13,   16,   75,   28,   24,   29,
 /*   120 */    31,    4,    1,    2,   11,   12,   54,   34,   15,   55,
 /*   130 */    51,   45,   46,   71,   57,   14,    5,   11,   12,   52,
 /*   140 */    34,   15,   62,  129,   45,   46,   71,   57,   14,    5,
 /*   150 */   101,  101,  129,   34,   18,  129,  129,   45,   46,  101,
 /*   160 */   101,   14,    5,  105,  129,  105,  105,  105,  105,   26,
 /*   170 */    27,    3,    4,    1,    2,  129,   41,   40,  129,  129,
 /*   180 */   129,   34,   20,  129,  105,   45,   46,   60,  129,   14,
 /*   190 */     5,  129,  129,   34,   20,  129,  129,   45,   46,   64,
 /*   200 */    48,   14,    5,  129,  129,   34,   20,   47,  129,   45,
 /*   210 */    46,   68,  129,   14,    5,  129,  129,   34,   20,  129,
 /*   220 */   129,   45,   46,   70,  129,   14,    5,  129,  129,   39,
 /*   230 */    44,  129,   28,   24,   29,   31,   59,  129,  129,   61,
 /*   240 */   129,   28,   24,   29,   31,  129,  129,   63,    9,   10,
 /*   250 */    61,  129,   28,   24,   29,   31,   67,   65,   58,   61,
 /*   260 */   129,   28,   24,   29,   31,   69,  129,  129,   61,  129,
 /*   270 */    28,   24,   29,   31,   34,   18,  129,  129,   45,   46,
 /*   280 */   129,  129,   14,    5,   66,   44,  129,   28,   24,   29,
 /*   290 */    31,  106,  129,  106,  106,  106,  106,  129,   26,   27,
 /*   300 */   129,  129,  129,  129,  129,   41,   40,  129,  129,  129,
 /*   310 */   129,  129,  106,
};
static const YYCODETYPE yy_lookahead[] = {
 /*     0 */    24,   25,   26,   27,   28,   29,   30,   31,   32,   12,
 /*    10 */    34,   35,   36,   37,    5,    4,    5,    8,    9,   10,
 /*    20 */    11,   12,   33,    0,   15,   16,   17,   18,   19,   20,
 /*    30 */    25,   26,   27,   28,   29,   30,   31,   32,   12,   34,
 /*    40 */    35,   36,   37,   25,   26,   27,   28,   29,   30,   31,
 /*    50 */    32,   12,   34,   35,   36,   37,   25,   26,   27,   28,
 /*    60 */    29,   30,   31,   32,   14,   34,   35,   36,   37,   25,
 /*    70 */    26,   27,   28,   29,   30,   31,   32,    6,   34,   35,
 /*    80 */    36,   37,   25,   26,   27,   28,   29,   30,   31,   32,
 /*    90 */    12,   34,   35,   36,   37,   25,   26,   27,   28,   29,
 /*   100 */    30,   31,   32,    7,   34,   35,   36,   37,   25,   26,
 /*   110 */    27,   28,   29,   30,   31,   32,    0,   34,   35,   36,
 /*   120 */    37,    3,    4,    5,    8,    9,   12,   11,   12,   21,
 /*   130 */    13,   15,   16,   17,   18,   19,   20,    8,    9,   22,
 /*   140 */    11,   12,   12,   38,   15,   16,   17,   18,   19,   20,
 /*   150 */     8,    9,   38,   11,   12,   38,   38,   15,   16,   17,
 /*   160 */    18,   19,   20,    0,   38,    2,    3,    4,    5,    6,
 /*   170 */     7,    2,    3,    4,    5,   38,   13,   14,   38,   38,
 /*   180 */    38,   11,   12,   38,   21,   15,   16,   17,   38,   19,
 /*   190 */    20,   38,   38,   11,   12,   38,   38,   15,   16,   17,
 /*   200 */    12,   19,   20,   38,   38,   11,   12,   19,   38,   15,
 /*   210 */    16,   17,   38,   19,   20,   38,   38,   11,   12,   38,
 /*   220 */    38,   15,   16,   17,   38,   19,   20,   38,   38,   31,
 /*   230 */    32,   38,   34,   35,   36,   37,   29,   38,   38,   32,
 /*   240 */    38,   34,   35,   36,   37,   38,   38,   29,    8,    9,
 /*   250 */    32,   38,   34,   35,   36,   37,   29,   17,   18,   32,
 /*   260 */    38,   34,   35,   36,   37,   29,   38,   38,   32,   38,
 /*   270 */    34,   35,   36,   37,   11,   12,   38,   38,   15,   16,
 /*   280 */    38,   38,   19,   20,   31,   32,   38,   34,   35,   36,
 /*   290 */    37,    0,   38,    2,    3,    4,    5,   38,    6,    7,
 /*   300 */    38,   38,   38,   38,   38,   13,   14,   38,   38,   38,
 /*   310 */    38,   38,   21,
};
#define YY_SHIFT_USE_DFLT (-4)
#define YY_SHIFT_MAX 34
static const short yy_shift_ofst[] = {
 /*     0 */   116,    9,  129,  129,  129,  129,  129,  129,  142,  170,
 /*    10 */   182,  194,  206,  263,   -3,  163,  291,  169,  292,  240,
 /*    20 */   292,  118,   11,  188,  117,   23,   26,   39,   50,   71,
 /*    30 */    78,   96,  114,  108,  130,
};
#define YY_REDUCE_USE_DFLT (-25)
#define YY_REDUCE_MAX 14
static const short yy_reduce_ofst[] = {
 /*     0 */   -24,    5,   18,   31,   44,   57,   70,   83,  198,  207,
 /*    10 */   218,  227,  236,  253,  -11,
};
static const YYACTIONTYPE yy_default[] = {
 /*     0 */    84,   84,   84,   84,   84,   84,   84,   84,   85,  127,
 /*    10 */   127,  127,  127,  102,  127,  103,  104,  127,  103,  127,
 /*    20 */   105,   81,   82,  127,  111,   83,  127,  127,  110,  112,
 /*    30 */   127,  113,  127,   83,  127,   76,   77,   78,   83,   90,
 /*    40 */   118,  120,  123,  125,  104,  107,  108,  109,  117,  116,
 /*    50 */   119,  121,  122,  124,  126,  114,   86,   87,   88,   92,
 /*    60 */   100,  106,  115,   94,   96,   98,   89,   91,   99,   93,
 /*    70 */    95,   97,   79,   80,
};
#define YY_SZ_ACTTAB (int)(sizeof(yy_action)/sizeof(yy_action[0]))

/* The next table maps tokens into fallback tokens.  If a construct
** like the following:
** 
**      %fallback ID X Y Z.
**
** appears in the grammar, then ID becomes a fallback token for X, Y,
** and Z.  Whenever one of the tokens X, Y, or Z is input to the parser
** but it does not parse, the type of the token is changed to ID and
** the parse is retried before an error is thrown.
*/
#ifdef YYFALLBACK
static const YYCODETYPE yyFallback[] = {
};
#endif /* YYFALLBACK */

/* The following structure represents a single element of the
** parser's stack.  Information stored includes:
**
**   +  The state number for the parser at this level of the stack.
**
**   +  The value of the token stored at this level of the stack.
**      (In other words, the "major" token.)
**
**   +  The semantic value stored at this level of the stack.  This is
**      the information used by the action routines in the grammar.
**      It is sometimes called the "minor" token.
*/
struct yyStackEntry {
  yyStackEntry() {
    stateno = 0;
    major = 0;
  }
  yyStackEntry(YYACTIONTYPE stateno_, YYCODETYPE major_, YYMINORTYPE minor_) {
    stateno = stateno_;
    major = major_;
    minor = minor_;
  }
  YYACTIONTYPE stateno;  /* The state-number */
  YYCODETYPE major;       /* The major token value.  This is the code
                          ** number for the token at this stack level */
  YYMINORTYPE minor;      /* The user-supplied minor token value.  This
                          ** is the value of the token  */
};

/* The state of the parser is completely contained in an instance of
** the following structure */
struct yyParser {
  int yyerrcnt;                 /* Shifts left before out of the error */
  ParseARG_SDECL                /* A place to hold %extra_argument */
  vector<yyStackEntry> yystack; /* The parser's stack */
};
typedef struct yyParser yyParser;

#include "omassert.h"
#include "debuglog.h"

#ifdef XAPIAN_DEBUG_LOG
/* For tracing shifts, the names of all terminals and nonterminals
** are required.  The following table supplies these names */
static const char *const yyTokenName[] = {
  "$",             "ERROR",         "OR",            "XOR",         
  "AND",           "NOT",           "NEAR",          "ADJ",         
  "LOVE",          "HATE",          "HATE_AFTER_AND",  "SYNONYM",     
  "TERM",          "GROUP_TERM",    "PHR_TERM",      "WILD_TERM",   
  "PARTIAL_TERM",  "BOOLEAN_FILTER",  "RANGE",         "QUOTE",       
  "BRA",           "KET",           "EMPTY_GROUP_OK",  "error",       
  "query",         "expr",          "prob_expr",     "bool_arg",    
  "prob",          "term",          "stop_prob",     "stop_term",   
  "compound_term",  "phrase",        "phrased_term",  "group",       
  "near_expr",     "adj_expr",    
};

/* For tracing reduce actions, the names of all rules are required.
*/
static const char *const yyRuleName[] = {
 /*   0 */ "query ::= expr",
 /*   1 */ "query ::=",
 /*   2 */ "expr ::= prob_expr",
 /*   3 */ "expr ::= bool_arg AND bool_arg",
 /*   4 */ "expr ::= bool_arg NOT bool_arg",
 /*   5 */ "expr ::= bool_arg AND NOT bool_arg",
 /*   6 */ "expr ::= bool_arg AND HATE_AFTER_AND bool_arg",
 /*   7 */ "expr ::= bool_arg OR bool_arg",
 /*   8 */ "expr ::= bool_arg XOR bool_arg",
 /*   9 */ "bool_arg ::= expr",
 /*  10 */ "bool_arg ::=",
 /*  11 */ "prob_expr ::= prob",
 /*  12 */ "prob_expr ::= term",
 /*  13 */ "prob ::= RANGE",
 /*  14 */ "prob ::= stop_prob RANGE",
 /*  15 */ "prob ::= stop_term stop_term",
 /*  16 */ "prob ::= prob stop_term",
 /*  17 */ "prob ::= LOVE term",
 /*  18 */ "prob ::= stop_prob LOVE term",
 /*  19 */ "prob ::= HATE term",
 /*  20 */ "prob ::= stop_prob HATE term",
 /*  21 */ "prob ::= HATE BOOLEAN_FILTER",
 /*  22 */ "prob ::= stop_prob HATE BOOLEAN_FILTER",
 /*  23 */ "prob ::= BOOLEAN_FILTER",
 /*  24 */ "prob ::= stop_prob BOOLEAN_FILTER",
 /*  25 */ "prob ::= LOVE BOOLEAN_FILTER",
 /*  26 */ "prob ::= stop_prob LOVE BOOLEAN_FILTER",
 /*  27 */ "stop_prob ::= prob",
 /*  28 */ "stop_prob ::= stop_term",
 /*  29 */ "stop_term ::= TERM",
 /*  30 */ "stop_term ::= compound_term",
 /*  31 */ "term ::= TERM",
 /*  32 */ "term ::= compound_term",
 /*  33 */ "compound_term ::= WILD_TERM",
 /*  34 */ "compound_term ::= PARTIAL_TERM",
 /*  35 */ "compound_term ::= QUOTE phrase QUOTE",
 /*  36 */ "compound_term ::= phrased_term",
 /*  37 */ "compound_term ::= group",
 /*  38 */ "compound_term ::= near_expr",
 /*  39 */ "compound_term ::= adj_expr",
 /*  40 */ "compound_term ::= BRA expr KET",
 /*  41 */ "compound_term ::= SYNONYM TERM",
 /*  42 */ "phrase ::= TERM",
 /*  43 */ "phrase ::= phrase TERM",
 /*  44 */ "phrased_term ::= TERM PHR_TERM",
 /*  45 */ "phrased_term ::= phrased_term PHR_TERM",
 /*  46 */ "group ::= TERM GROUP_TERM",
 /*  47 */ "group ::= group GROUP_TERM",
 /*  48 */ "group ::= group EMPTY_GROUP_OK",
 /*  49 */ "near_expr ::= TERM NEAR TERM",
 /*  50 */ "near_expr ::= near_expr NEAR TERM",
 /*  51 */ "adj_expr ::= TERM ADJ TERM",
 /*  52 */ "adj_expr ::= adj_expr ADJ TERM",
};

/*
** This function returns the symbolic name associated with a token
** value.
*/
static const char *ParseTokenName(int tokenType){
  if( tokenType>=0 && tokenType<(int)(sizeof(yyTokenName)/sizeof(yyTokenName[0])) ){
    return yyTokenName[tokenType];
  }
  return "Unknown";
}

/*
** This function returns the symbolic name associated with a rule
** value.
*/
static const char *ParseRuleName(int ruleNum){
  if( ruleNum>=0 && ruleNum<(int)(sizeof(yyRuleName)/sizeof(yyRuleName[0])) ){
    return yyRuleName[ruleNum];
  }
  return "Unknown";
}
#endif /* XAPIAN_DEBUG_LOG */

/* 
** This function allocates a new parser.
** The only argument is a pointer to a function which works like
** malloc.
**
** Inputs:
** None.
**
** Outputs:
** A pointer to a parser.  This pointer is used in subsequent calls
** to Parse and ParseFree.
*/
static yyParser *ParseAlloc(){
  return new yyParser;
}

/* The following function deletes the value associated with a
** symbol.  The symbol can be either a terminal or nonterminal.
** "yymajor" is the symbol code, and "yypminor" is a pointer to
** the value.
*/
static void yy_destructor(
  yyParser *yypParser,    /* The parser */
  YYCODETYPE yymajor,     /* Type code for object to destroy */
  YYMINORTYPE *yypminor   /* The object to be destroyed */
){
  ParseARG_FETCH;
  switch( yymajor ){
    /* Here is inserted the actions which take place when a
    ** terminal or non-terminal is destroyed.  This can happen
    ** when the symbol is popped from the stack during a
    ** reduce or during error processing or when a parser is 
    ** being destroyed before it is finished parsing.
    **
    ** Note: during a reduce, the only symbols destroyed are those
    ** which appear on the RHS of the rule, but which are not used
    ** inside the C code.
    */
      /* TERMINAL Destructor */
    case 1: /* ERROR */
    case 2: /* OR */
    case 3: /* XOR */
    case 4: /* AND */
    case 5: /* NOT */
    case 6: /* NEAR */
    case 7: /* ADJ */
    case 8: /* LOVE */
    case 9: /* HATE */
    case 10: /* HATE_AFTER_AND */
    case 11: /* SYNONYM */
    case 12: /* TERM */
    case 13: /* GROUP_TERM */
    case 14: /* PHR_TERM */
    case 15: /* WILD_TERM */
    case 16: /* PARTIAL_TERM */
    case 17: /* BOOLEAN_FILTER */
    case 18: /* RANGE */
    case 19: /* QUOTE */
    case 20: /* BRA */
    case 21: /* KET */
    case 22: /* EMPTY_GROUP_OK */
{
#line 1570 "queryparser/queryparser.lemony"
delete (yypminor->yy0);
#line 2023 "queryparser/queryparser_internal.cc"
}
      break;
    case 25: /* expr */
    case 26: /* prob_expr */
    case 27: /* bool_arg */
    case 29: /* term */
    case 31: /* stop_term */
    case 32: /* compound_term */
{
#line 1645 "queryparser/queryparser.lemony"
delete (yypminor->yy73);
#line 2035 "queryparser/queryparser_internal.cc"
}
      break;
    case 28: /* prob */
    case 30: /* stop_prob */
{
#line 1740 "queryparser/queryparser.lemony"
delete (yypminor->yy12);
#line 2043 "queryparser/queryparser_internal.cc"
}
      break;
    case 33: /* phrase */
    case 34: /* phrased_term */
    case 36: /* near_expr */
    case 37: /* adj_expr */
{
#line 1941 "queryparser/queryparser.lemony"
(yypminor->yy46)->destroy();
#line 2053 "queryparser/queryparser_internal.cc"
}
      break;
    case 35: /* group */
{
#line 1975 "queryparser/queryparser.lemony"
(yypminor->yy76)->destroy();
#line 2060 "queryparser/queryparser_internal.cc"
}
      break;
    default:  break;   /* If no destructor action specified: do nothing */
  }
  ParseARG_STORE; /* Suppress warning about unused %extra_argument variable */
}

/*
** Pop the parser's stack once.
**
** If there is a destructor routine associated with the token which
** is popped from the stack, then call it.
**
** Return the major token number for the symbol popped.
*/
static int yy_pop_parser_stack(yyParser *pParser){
  YYCODETYPE yymajor;
  if( pParser->yystack.empty() ) return 0;
  yyStackEntry *yytos = &pParser->yystack.back();

  LOGLINE(QUERYPARSER, "Popping " << ParseTokenName(yytos->major));
  yymajor = (YYCODETYPE)yytos->major;
  yy_destructor(pParser, yymajor, &yytos->minor);
  pParser->yystack.pop_back();
  return yymajor;
}

/* 
** Deallocate and destroy a parser.  Destructors are all called for
** all stack elements before shutting the parser down.
**
** Inputs:
** A pointer to the parser.  This should be a pointer
** obtained from ParseAlloc.
*/
static void ParseFree(
  yyParser *pParser           /* The parser to be deleted */
){
  if( pParser==0 ) return;
  while( !pParser->yystack.empty() ) yy_pop_parser_stack(pParser);
  delete pParser;
}

/*
** Find the appropriate action for a parser given the terminal
** look-ahead token iLookAhead.
**
** If the look-ahead token is YYNOCODE, then check to see if the action is
** independent of the look-ahead.  If it is, return the action, otherwise
** return YY_NO_ACTION.
*/
static int yy_find_shift_action(
  yyParser *pParser,        /* The parser */
  YYCODETYPE iLookAhead     /* The look-ahead token */
){
  int i;
  int stateno = pParser->yystack.back().stateno;
 
  if( stateno>YY_SHIFT_MAX || (i = yy_shift_ofst[stateno])==YY_SHIFT_USE_DFLT ){
    return yy_default[stateno];
  }
  Assert( iLookAhead!=YYNOCODE );
  i += iLookAhead;
  if( i<0 || i>=YY_SZ_ACTTAB || yy_lookahead[i]!=iLookAhead ){
    if( iLookAhead>0 ){
#ifdef YYFALLBACK
      YYCODETYPE iFallback;            /* Fallback token */
      if( iLookAhead<sizeof(yyFallback)/sizeof(yyFallback[0])
             && (iFallback = yyFallback[iLookAhead])!=0 ){
        LOGLINE(QUERYPARSER,
		"FALLBACK " << ParseTokenName(iLookAhead) << " => " <<
		ParseTokenName(iFallback));
        return yy_find_shift_action(pParser, iFallback);
      }
#endif
#ifdef YYWILDCARD
      {
        int j = i - iLookAhead + YYWILDCARD;
        if( j>=0 && j<YY_SZ_ACTTAB && yy_lookahead[j]==YYWILDCARD ){
	  LOGLINE(QUERYPARSER,
		  "WILDCARD " << ParseTokenName(iLookAhead) << " => " <<
		  ParseTokenName(YYWILDCARD));
	  return yy_action[j];
	}
      }
#endif /* YYWILDCARD */
    }
    return yy_default[stateno];
  }else{
    return yy_action[i];
  }
}

/*
** Find the appropriate action for a parser given the non-terminal
** look-ahead token iLookAhead.
**
** If the look-ahead token is YYNOCODE, then check to see if the action is
** independent of the look-ahead.  If it is, return the action, otherwise
** return YY_NO_ACTION.
*/
static int yy_find_reduce_action(
  int stateno,              /* Current state number */
  YYCODETYPE iLookAhead     /* The look-ahead token */
){
  int i;
#ifdef YYERRORSYMBOL
  if( stateno>YY_REDUCE_MAX ){
    return yy_default[stateno];
  }
#else
  Assert( stateno<=YY_REDUCE_MAX );
#endif
  i = yy_reduce_ofst[stateno];
  Assert( i!=YY_REDUCE_USE_DFLT );
  Assert( iLookAhead!=YYNOCODE );
  i += iLookAhead;
#ifdef YYERRORSYMBOL
  if( i<0 || i>=YY_SZ_ACTTAB || yy_lookahead[i]!=iLookAhead ){
    return yy_default[stateno];
  }
#else
  Assert( i>=0 && i<YY_SZ_ACTTAB );
  Assert( yy_lookahead[i]==iLookAhead );
#endif
  return yy_action[i];
}

/*
** Perform a shift action.
*/
static void yy_shift(
  yyParser *yypParser,          /* The parser to be shifted */
  int yyNewState,               /* The new state to shift in */
  int yyMajor,                  /* The major token to shift in */
  YYMINORTYPE *yypMinor         /* Pointer to the minor token to shift in */
){
  /* Here code is inserted which will execute if the parser
  ** stack every overflows.  We use std::vector<> for our stack
  ** so we'll never need this code.
  */
#if 0
#endif
#ifdef XAPIAN_DEBUG_LOG
  unsigned i;
  LOGLINE(QUERYPARSER, "Shift " << yyNewState);
  string stack("Stack:");
  for (i = 0; i < yypParser->yystack.size(); i++) {
    stack += ' ';
    stack += ParseTokenName(yypParser->yystack[i].major);
  }
  LOGLINE(QUERYPARSER, stack);
#endif
  yypParser->yystack.push_back(yyStackEntry(yyNewState, yyMajor, *yypMinor));
}

/* The following table contains information about every rule that
** is used during the reduce.
*/
static const struct {
  YYCODETYPE lhs;         /* Symbol on the left-hand side of the rule */
  unsigned char nrhs;     /* Number of right-hand side symbols in the rule */
} yyRuleInfo[] = {
  { 24, 1 },
  { 24, 0 },
  { 25, 1 },
  { 25, 3 },
  { 25, 3 },
  { 25, 4 },
  { 25, 4 },
  { 25, 3 },
  { 25, 3 },
  { 27, 1 },
  { 27, 0 },
  { 26, 1 },
  { 26, 1 },
  { 28, 1 },
  { 28, 2 },
  { 28, 2 },
  { 28, 2 },
  { 28, 2 },
  { 28, 3 },
  { 28, 2 },
  { 28, 3 },
  { 28, 2 },
  { 28, 3 },
  { 28, 1 },
  { 28, 2 },
  { 28, 2 },
  { 28, 3 },
  { 30, 1 },
  { 30, 1 },
  { 31, 1 },
  { 31, 1 },
  { 29, 1 },
  { 29, 1 },
  { 32, 1 },
  { 32, 1 },
  { 32, 3 },
  { 32, 1 },
  { 32, 1 },
  { 32, 1 },
  { 32, 1 },
  { 32, 3 },
  { 32, 2 },
  { 33, 1 },
  { 33, 2 },
  { 34, 2 },
  { 34, 2 },
  { 35, 2 },
  { 35, 2 },
  { 35, 2 },
  { 36, 3 },
  { 36, 3 },
  { 37, 3 },
  { 37, 3 },
};

static void yy_accept(yyParser*);  /* Forward Declaration */

/*
** Perform a reduce action and the shift that must immediately
** follow the reduce.
*/
static void yy_reduce(
  yyParser *yypParser,         /* The parser */
  int yyruleno                 /* Number of the rule by which to reduce */
){
  int yygoto;                     /* The next state */
  int yyact;                      /* The next action */
  YYMINORTYPE yygotominor;        /* The LHS of the rule reduced */
  yyStackEntry *yymsp;            /* The top of the parser's stack */
  int yysize;                     /* Amount to pop the stack */
  ParseARG_FETCH;
  yymsp = &yypParser->yystack.back();
#ifdef XAPIAN_DEBUG_LOG
  LOGLINE(QUERYPARSER, "Reduce [" << ParseRuleName(yyruleno) << "].");
#endif

  /* Silence complaints from purify about yygotominor being uninitialized
  ** in some cases when it is copied into the stack after the following
  ** switch.  yygotominor is uninitialized when a rule reduces that does
  ** not set the value of its left-hand side nonterminal.  Leaving the
  ** value of the nonterminal uninitialized is utterly harmless as long
  ** as the value is never used.  So really the only thing this code
  ** accomplishes is to quieten purify.  
  **
  ** 2007-01-16:  The wireshark project (www.wireshark.org) reports that
  ** without this code, their parser segfaults.  I'm not sure what there
  ** parser is doing to make this happen.  This is the second bug report
  ** from wireshark this week.  Clearly they are stressing Lemon in ways
  ** that it has not been previously stressed...  (SQLite ticket #2172)
  */
  /* Later comments on ticket #2172 note that this is a bug in wireshark's
   * grammar which lemon fails to diagnose, so commenting out for Xapian. */
  /* memset(&yygotominor, 0, sizeof(yygotominor)); */


  switch( yyruleno ){
  /* Beginning here are the reduction cases.  A typical example
  ** follows:
  **   case 0:
  **  #line <lineno> <grammarfile>
  **     { ... }           // User supplied code
  **  #line <lineno> <thisfile>
  **     break;
  */
      case 0: /* query ::= expr */
#line 1627 "queryparser/queryparser.lemony"
{
    // Save the parsed query in the State structure so we can return it.
    if (yymsp[0].minor.yy73) {
	state->query = *yymsp[0].minor.yy73;
	delete yymsp[0].minor.yy73;
    } else {
	state->query = Query();
    }
}
#line 2339 "queryparser/queryparser_internal.cc"
        break;
      case 1: /* query ::= */
#line 1637 "queryparser/queryparser.lemony"
{
    // Handle a query string with no terms in.
    state->query = Query();
}
#line 2347 "queryparser/queryparser_internal.cc"
        break;
      case 2: /* expr ::= prob_expr */
      case 9: /* bool_arg ::= expr */ yytestcase(yyruleno==9);
#line 1648 "queryparser/queryparser.lemony"
{ yygotominor.yy73 = yymsp[0].minor.yy73; }
#line 2353 "queryparser/queryparser_internal.cc"
        break;
      case 3: /* expr ::= bool_arg AND bool_arg */
#line 1651 "queryparser/queryparser.lemony"
{ BOOL_OP_TO_QUERY(yygotominor.yy73, yymsp[-2].minor.yy73, Query::OP_AND, yymsp[0].minor.yy73, "AND");   yy_destructor(yypParser,4,&yymsp[-1].minor);
}
#line 2359 "queryparser/queryparser_internal.cc"
        break;
      case 4: /* expr ::= bool_arg NOT bool_arg */
#line 1653 "queryparser/queryparser.lemony"
{
    // 'NOT foo' -> '<alldocuments> NOT foo'
    if (!yymsp[-2].minor.yy73 && (state->flags & QueryParser::FLAG_PURE_NOT)) {
	yymsp[-2].minor.yy73 = new Query("", 1, 0);
    }
    BOOL_OP_TO_QUERY(yygotominor.yy73, yymsp[-2].minor.yy73, Query::OP_AND_NOT, yymsp[0].minor.yy73, "NOT");
  yy_destructor(yypParser,5,&yymsp[-1].minor);
}
#line 2371 "queryparser/queryparser_internal.cc"
        break;
      case 5: /* expr ::= bool_arg AND NOT bool_arg */
#line 1662 "queryparser/queryparser.lemony"
{ BOOL_OP_TO_QUERY(yygotominor.yy73, yymsp[-3].minor.yy73, Query::OP_AND_NOT, yymsp[0].minor.yy73, "AND NOT");   yy_destructor(yypParser,4,&yymsp[-2].minor);
  yy_destructor(yypParser,5,&yymsp[-1].minor);
}
#line 2378 "queryparser/queryparser_internal.cc"
        break;
      case 6: /* expr ::= bool_arg AND HATE_AFTER_AND bool_arg */
#line 1665 "queryparser/queryparser.lemony"
{ BOOL_OP_TO_QUERY(yygotominor.yy73, yymsp[-3].minor.yy73, Query::OP_AND_NOT, yymsp[0].minor.yy73, "AND");   yy_destructor(yypParser,4,&yymsp[-2].minor);
  yy_destructor(yypParser,10,&yymsp[-1].minor);
}
#line 2385 "queryparser/queryparser_internal.cc"
        break;
      case 7: /* expr ::= bool_arg OR bool_arg */
#line 1668 "queryparser/queryparser.lemony"
{ BOOL_OP_TO_QUERY(yygotominor.yy73, yymsp[-2].minor.yy73, Query::OP_OR, yymsp[0].minor.yy73, "OR");   yy_destructor(yypParser,2,&yymsp[-1].minor);
}
#line 2391 "queryparser/queryparser_internal.cc"
        break;
      case 8: /* expr ::= bool_arg XOR bool_arg */
#line 1671 "queryparser/queryparser.lemony"
{ BOOL_OP_TO_QUERY(yygotominor.yy73, yymsp[-2].minor.yy73, Query::OP_XOR, yymsp[0].minor.yy73, "XOR");   yy_destructor(yypParser,3,&yymsp[-1].minor);
}
#line 2397 "queryparser/queryparser_internal.cc"
        break;
      case 10: /* bool_arg ::= */
#line 1680 "queryparser/queryparser.lemony"
{
    // Set the argument to NULL, which enables the bool_arg-using rules in
    // expr above to report uses of AND, OR, etc which don't have two
    // arguments.
    yygotominor.yy73 = NULL;
}
#line 2407 "queryparser/queryparser_internal.cc"
        break;
      case 11: /* prob_expr ::= prob */
#line 1692 "queryparser/queryparser.lemony"
{
    yygotominor.yy73 = yymsp[0].minor.yy12->query;
    yymsp[0].minor.yy12->query = NULL;
    // Handle any "+ terms".
    if (yymsp[0].minor.yy12->love) {
	if (yymsp[0].minor.yy12->love->empty()) {
	    // +<nothing>.
	    delete yygotominor.yy73;
	    yygotominor.yy73 = yymsp[0].minor.yy12->love;
	} else if (yygotominor.yy73) {
	    swap(yygotominor.yy73, yymsp[0].minor.yy12->love);
	    add_to_query(yygotominor.yy73, Query::OP_AND_MAYBE, yymsp[0].minor.yy12->love);
	} else {
	    yygotominor.yy73 = yymsp[0].minor.yy12->love;
	}
	yymsp[0].minor.yy12->love = NULL;
    }
    // Handle any boolean filters.
    if (!yymsp[0].minor.yy12->filter.empty()) {
	if (yygotominor.yy73) {
	    add_to_query(yygotominor.yy73, Query::OP_FILTER, yymsp[0].minor.yy12->merge_filters());
	} else {
	    // Make the query a boolean one.
	    yygotominor.yy73 = new Query(Query::OP_SCALE_WEIGHT, yymsp[0].minor.yy12->merge_filters(), 0.0);
	}
    }
    // Handle any "- terms".
    if (yymsp[0].minor.yy12->hate && !yymsp[0].minor.yy12->hate->empty()) {
	if (!yygotominor.yy73) {
	    // Can't just hate!
	    yy_parse_failed(yypParser);
	    return;
	}
	*yygotominor.yy73 = Query(Query::OP_AND_NOT, *yygotominor.yy73, *yymsp[0].minor.yy12->hate);
    }
    delete yymsp[0].minor.yy12;
}
#line 2448 "queryparser/queryparser_internal.cc"
        break;
      case 12: /* prob_expr ::= term */
      case 30: /* stop_term ::= compound_term */ yytestcase(yyruleno==30);
      case 32: /* term ::= compound_term */ yytestcase(yyruleno==32);
#line 1730 "queryparser/queryparser.lemony"
{
    yygotominor.yy73 = yymsp[0].minor.yy73;
}
#line 2457 "queryparser/queryparser_internal.cc"
        break;
      case 13: /* prob ::= RANGE */
#line 1742 "queryparser/queryparser.lemony"
{
    valueno slot = yymsp[0].minor.yy0->pos;
    const Query & range = yymsp[0].minor.yy0->as_value_range_query();
    yygotominor.yy12 = new ProbQuery;
    yygotominor.yy12->add_filter_range(slot, range);
}
#line 2467 "queryparser/queryparser_internal.cc"
        break;
      case 14: /* prob ::= stop_prob RANGE */
#line 1749 "queryparser/queryparser.lemony"
{
    valueno slot = yymsp[0].minor.yy0->pos;
    const Query & range = yymsp[0].minor.yy0->as_value_range_query();
    yygotominor.yy12 = yymsp[-1].minor.yy12;
    yygotominor.yy12->append_filter_range(slot, range);
}
#line 2477 "queryparser/queryparser_internal.cc"
        break;
      case 15: /* prob ::= stop_term stop_term */
#line 1756 "queryparser/queryparser.lemony"
{
    yygotominor.yy12 = new ProbQuery;
    yygotominor.yy12->query = yymsp[-1].minor.yy73;
    if (yymsp[0].minor.yy73) {
	Query::op op = state->default_op();
	if (yygotominor.yy12->query && is_positional(op)) {
	    // If default_op is OP_NEAR or OP_PHRASE, set the window size to
	    // 11 for the first pair of terms and it will automatically grow
	    // by one for each subsequent term.
	    Query * subqs[2] = { yygotominor.yy12->query, yymsp[0].minor.yy73 };
	    *(yygotominor.yy12->query) = Query(op, subqs, subqs + 2, 11);
	    delete yymsp[0].minor.yy73;
	} else {
	    add_to_query(yygotominor.yy12->query, op, yymsp[0].minor.yy73);
	}
    }
}
#line 2498 "queryparser/queryparser_internal.cc"
        break;
      case 16: /* prob ::= prob stop_term */
#line 1774 "queryparser/queryparser.lemony"
{
    yygotominor.yy12 = yymsp[-1].minor.yy12;
    // If yymsp[0].minor.yy73 is a stopword, there's nothing to do here.
    if (yymsp[0].minor.yy73) add_to_query(yygotominor.yy12->query, state->default_op(), yymsp[0].minor.yy73);
}
#line 2507 "queryparser/queryparser_internal.cc"
        break;
      case 17: /* prob ::= LOVE term */
#line 1780 "queryparser/queryparser.lemony"
{
    yygotominor.yy12 = new ProbQuery;
    if (state->default_op() == Query::OP_AND) {
	yygotominor.yy12->query = yymsp[0].minor.yy73;
    } else {
	yygotominor.yy12->love = yymsp[0].minor.yy73;
    }
  yy_destructor(yypParser,8,&yymsp[-1].minor);
}
#line 2520 "queryparser/queryparser_internal.cc"
        break;
      case 18: /* prob ::= stop_prob LOVE term */
#line 1789 "queryparser/queryparser.lemony"
{
    yygotominor.yy12 = yymsp[-2].minor.yy12;
    if (state->default_op() == Query::OP_AND) {
	/* The default op is AND, so we just put loved terms into the query
	 * (in this case the only effect of love is to ignore the stopword
	 * list). */
	add_to_query(yygotominor.yy12->query, Query::OP_AND, yymsp[0].minor.yy73);
    } else {
	add_to_query(yygotominor.yy12->love, Query::OP_AND, yymsp[0].minor.yy73);
    }
  yy_destructor(yypParser,8,&yymsp[-1].minor);
}
#line 2536 "queryparser/queryparser_internal.cc"
        break;
      case 19: /* prob ::= HATE term */
#line 1801 "queryparser/queryparser.lemony"
{
    yygotominor.yy12 = new ProbQuery;
    yygotominor.yy12->hate = yymsp[0].minor.yy73;
  yy_destructor(yypParser,9,&yymsp[-1].minor);
}
#line 2545 "queryparser/queryparser_internal.cc"
        break;
      case 20: /* prob ::= stop_prob HATE term */
#line 1806 "queryparser/queryparser.lemony"
{
    yygotominor.yy12 = yymsp[-2].minor.yy12;
    add_to_query(yygotominor.yy12->hate, Query::OP_OR, yymsp[0].minor.yy73);
  yy_destructor(yypParser,9,&yymsp[-1].minor);
}
#line 2554 "queryparser/queryparser_internal.cc"
        break;
      case 21: /* prob ::= HATE BOOLEAN_FILTER */
#line 1811 "queryparser/queryparser.lemony"
{
    yygotominor.yy12 = new ProbQuery;
    yygotominor.yy12->hate = new Query(yymsp[0].minor.yy0->get_query());
    delete yymsp[0].minor.yy0;
  yy_destructor(yypParser,9,&yymsp[-1].minor);
}
#line 2564 "queryparser/queryparser_internal.cc"
        break;
      case 22: /* prob ::= stop_prob HATE BOOLEAN_FILTER */
#line 1817 "queryparser/queryparser.lemony"
{
    yygotominor.yy12 = yymsp[-2].minor.yy12;
    add_to_query(yygotominor.yy12->hate, Query::OP_OR, yymsp[0].minor.yy0->get_query());
    delete yymsp[0].minor.yy0;
  yy_destructor(yypParser,9,&yymsp[-1].minor);
}
#line 2574 "queryparser/queryparser_internal.cc"
        break;
      case 23: /* prob ::= BOOLEAN_FILTER */
#line 1823 "queryparser/queryparser.lemony"
{
    yygotominor.yy12 = new ProbQuery;
    yygotominor.yy12->add_filter(yymsp[0].minor.yy0->get_filter_group_id(), yymsp[0].minor.yy0->get_query());
    delete yymsp[0].minor.yy0;
}
#line 2583 "queryparser/queryparser_internal.cc"
        break;
      case 24: /* prob ::= stop_prob BOOLEAN_FILTER */
#line 1829 "queryparser/queryparser.lemony"
{
    yygotominor.yy12 = yymsp[-1].minor.yy12;
    yygotominor.yy12->append_filter(yymsp[0].minor.yy0->get_filter_group_id(), yymsp[0].minor.yy0->get_query());
    delete yymsp[0].minor.yy0;
}
#line 2592 "queryparser/queryparser_internal.cc"
        break;
      case 25: /* prob ::= LOVE BOOLEAN_FILTER */
#line 1835 "queryparser/queryparser.lemony"
{
    // LOVE BOOLEAN_FILTER(yymsp[0].minor.yy0) is just the same as BOOLEAN_FILTER
    yygotominor.yy12 = new ProbQuery;
    yygotominor.yy12->filter[yymsp[0].minor.yy0->get_filter_group_id()] = yymsp[0].minor.yy0->get_query();
    delete yymsp[0].minor.yy0;
  yy_destructor(yypParser,8,&yymsp[-1].minor);
}
#line 2603 "queryparser/queryparser_internal.cc"
        break;
      case 26: /* prob ::= stop_prob LOVE BOOLEAN_FILTER */
#line 1842 "queryparser/queryparser.lemony"
{
    // LOVE BOOLEAN_FILTER(yymsp[0].minor.yy0) is just the same as BOOLEAN_FILTER
    yygotominor.yy12 = yymsp[-2].minor.yy12;
    // We OR filters with the same prefix...
    Query & q = yygotominor.yy12->filter[yymsp[0].minor.yy0->get_filter_group_id()];
    q = Query(Query::OP_OR, q, yymsp[0].minor.yy0->get_query());
    delete yymsp[0].minor.yy0;
  yy_destructor(yypParser,8,&yymsp[-1].minor);
}
#line 2616 "queryparser/queryparser_internal.cc"
        break;
      case 27: /* stop_prob ::= prob */
#line 1857 "queryparser/queryparser.lemony"
{ yygotominor.yy12 = yymsp[0].minor.yy12; }
#line 2621 "queryparser/queryparser_internal.cc"
        break;
      case 28: /* stop_prob ::= stop_term */
#line 1859 "queryparser/queryparser.lemony"
{
    yygotominor.yy12 = new ProbQuery;
    yygotominor.yy12->query = yymsp[0].minor.yy73;
}
#line 2629 "queryparser/queryparser_internal.cc"
        break;
      case 29: /* stop_term ::= TERM */
#line 1873 "queryparser/queryparser.lemony"
{
    if (state->is_stopword(yymsp[0].minor.yy0)) {
	yygotominor.yy73 = NULL;
	state->add_to_stoplist(yymsp[0].minor.yy0);
    } else {
	yygotominor.yy73 = new Query(yymsp[0].minor.yy0->get_query_with_auto_synonyms());
    }
    delete yymsp[0].minor.yy0;
}
#line 2642 "queryparser/queryparser_internal.cc"
        break;
      case 31: /* term ::= TERM */
#line 1892 "queryparser/queryparser.lemony"
{
    yygotominor.yy73 = new Query(yymsp[0].minor.yy0->get_query_with_auto_synonyms());
    delete yymsp[0].minor.yy0;
}
#line 2650 "queryparser/queryparser_internal.cc"
        break;
      case 33: /* compound_term ::= WILD_TERM */
#line 1909 "queryparser/queryparser.lemony"
{ yygotominor.yy73 = yymsp[0].minor.yy0->as_wildcarded_query(state); }
#line 2655 "queryparser/queryparser_internal.cc"
        break;
      case 34: /* compound_term ::= PARTIAL_TERM */
#line 1912 "queryparser/queryparser.lemony"
{ yygotominor.yy73 = yymsp[0].minor.yy0->as_partial_query(state); }
#line 2660 "queryparser/queryparser_internal.cc"
        break;
      case 35: /* compound_term ::= QUOTE phrase QUOTE */
#line 1915 "queryparser/queryparser.lemony"
{ yygotominor.yy73 = yymsp[-1].minor.yy46->as_phrase_query();   yy_destructor(yypParser,19,&yymsp[-2].minor);
  yy_destructor(yypParser,19,&yymsp[0].minor);
}
#line 2667 "queryparser/queryparser_internal.cc"
        break;
      case 36: /* compound_term ::= phrased_term */
#line 1918 "queryparser/queryparser.lemony"
{ yygotominor.yy73 = yymsp[0].minor.yy46->as_phrase_query(); }
#line 2672 "queryparser/queryparser_internal.cc"
        break;
      case 37: /* compound_term ::= group */
#line 1921 "queryparser/queryparser.lemony"
{ yygotominor.yy73 = yymsp[0].minor.yy76->as_group(state); }
#line 2677 "queryparser/queryparser_internal.cc"
        break;
      case 38: /* compound_term ::= near_expr */
#line 1924 "queryparser/queryparser.lemony"
{ yygotominor.yy73 = yymsp[0].minor.yy46->as_near_query(); }
#line 2682 "queryparser/queryparser_internal.cc"
        break;
      case 39: /* compound_term ::= adj_expr */
#line 1927 "queryparser/queryparser.lemony"
{ yygotominor.yy73 = yymsp[0].minor.yy46->as_adj_query(); }
#line 2687 "queryparser/queryparser_internal.cc"
        break;
      case 40: /* compound_term ::= BRA expr KET */
#line 1930 "queryparser/queryparser.lemony"
{ yygotominor.yy73 = yymsp[-1].minor.yy73;   yy_destructor(yypParser,20,&yymsp[-2].minor);
  yy_destructor(yypParser,21,&yymsp[0].minor);
}
#line 2694 "queryparser/queryparser_internal.cc"
        break;
      case 41: /* compound_term ::= SYNONYM TERM */
#line 1932 "queryparser/queryparser.lemony"
{
    yygotominor.yy73 = new Query(yymsp[0].minor.yy0->get_query_with_synonyms());
    delete yymsp[0].minor.yy0;
  yy_destructor(yypParser,11,&yymsp[-1].minor);
}
#line 2703 "queryparser/queryparser_internal.cc"
        break;
      case 42: /* phrase ::= TERM */
#line 1943 "queryparser/queryparser.lemony"
{
    yygotominor.yy46 = new Terms;
    yygotominor.yy46->add_positional_term(yymsp[0].minor.yy0);
}
#line 2711 "queryparser/queryparser_internal.cc"
        break;
      case 43: /* phrase ::= phrase TERM */
      case 45: /* phrased_term ::= phrased_term PHR_TERM */ yytestcase(yyruleno==45);
#line 1948 "queryparser/queryparser.lemony"
{
    yygotominor.yy46 = yymsp[-1].minor.yy46;
    yygotominor.yy46->add_positional_term(yymsp[0].minor.yy0);
}
#line 2720 "queryparser/queryparser_internal.cc"
        break;
      case 44: /* phrased_term ::= TERM PHR_TERM */
#line 1960 "queryparser/queryparser.lemony"
{
    yygotominor.yy46 = new Terms;
    yygotominor.yy46->add_positional_term(yymsp[-1].minor.yy0);
    yygotominor.yy46->add_positional_term(yymsp[0].minor.yy0);
}
#line 2729 "queryparser/queryparser_internal.cc"
        break;
      case 46: /* group ::= TERM GROUP_TERM */
#line 1977 "queryparser/queryparser.lemony"
{
    yygotominor.yy76 = new TermGroup;
    yygotominor.yy76->add_term(yymsp[-1].minor.yy0);
    yygotominor.yy76->add_term(yymsp[0].minor.yy0);
}
#line 2738 "queryparser/queryparser_internal.cc"
        break;
      case 47: /* group ::= group GROUP_TERM */
#line 1983 "queryparser/queryparser.lemony"
{
    yygotominor.yy76 = yymsp[-1].minor.yy76;
    yygotominor.yy76->add_term(yymsp[0].minor.yy0);
}
#line 2746 "queryparser/queryparser_internal.cc"
        break;
      case 48: /* group ::= group EMPTY_GROUP_OK */
#line 1988 "queryparser/queryparser.lemony"
{
    yygotominor.yy76 = yymsp[-1].minor.yy76;
    yygotominor.yy76->set_empty_ok();
  yy_destructor(yypParser,22,&yymsp[0].minor);
}
#line 2755 "queryparser/queryparser_internal.cc"
        break;
      case 49: /* near_expr ::= TERM NEAR TERM */
      case 51: /* adj_expr ::= TERM ADJ TERM */ yytestcase(yyruleno==51);
#line 1999 "queryparser/queryparser.lemony"
{
    yygotominor.yy46 = new Terms;
    yygotominor.yy46->add_positional_term(yymsp[-2].minor.yy0);
    yygotominor.yy46->add_positional_term(yymsp[0].minor.yy0);
    if (yymsp[-1].minor.yy0) {
	yygotominor.yy46->adjust_window(yymsp[-1].minor.yy0->get_termpos());
	delete yymsp[-1].minor.yy0;
    }
}
#line 2769 "queryparser/queryparser_internal.cc"
        break;
      case 50: /* near_expr ::= near_expr NEAR TERM */
      case 52: /* adj_expr ::= adj_expr ADJ TERM */ yytestcase(yyruleno==52);
#line 2009 "queryparser/queryparser.lemony"
{
    yygotominor.yy46 = yymsp[-2].minor.yy46;
    yygotominor.yy46->add_positional_term(yymsp[0].minor.yy0);
    if (yymsp[-1].minor.yy0) {
	yygotominor.yy46->adjust_window(yymsp[-1].minor.yy0->get_termpos());
	delete yymsp[-1].minor.yy0;
    }
}
#line 2782 "queryparser/queryparser_internal.cc"
        break;
      default:
        break;
  }
  yygoto = yyRuleInfo[yyruleno].lhs;
  yysize = yyRuleInfo[yyruleno].nrhs;
  yypParser->yystack.resize(yypParser->yystack.size() - yysize);
  yyact = yy_find_reduce_action(yypParser->yystack.back().stateno,(YYCODETYPE)yygoto);
  if( yyact < YYNSTATE ){
    yy_shift(yypParser,yyact,yygoto,&yygotominor);
  }else{
    Assert( yyact == YYNSTATE + YYNRULE + 1 );
    yy_accept(yypParser);
  }
}

/*
** The following code executes when the parse fails
*/
#ifndef YYNOERRORRECOVERY
static void yy_parse_failed(
  yyParser *yypParser           /* The parser */
){
  ParseARG_FETCH;
  LOGLINE(QUERYPARSER, "Fail!");
  while( !yypParser->yystack.empty() ) yy_pop_parser_stack(yypParser);
  /* Here code is inserted which will be executed whenever the
  ** parser fails */
#line 1574 "queryparser/queryparser.lemony"

    // If we've not already set an error message, set a default one.
    if (!state->error) state->error = "parse error";
#line 2815 "queryparser/queryparser_internal.cc"
  ParseARG_STORE; /* Suppress warning about unused %extra_argument variable */
}
#endif /* YYNOERRORRECOVERY */

/*
** The following code executes when a syntax error first occurs.
*/
static void yy_syntax_error(
  yyParser *yypParser,           /* The parser */
  int yymajor,                   /* The major type of the error token */
  YYMINORTYPE yyminor            /* The minor type of the error token */
){
  ParseARG_FETCH;
  (void)yymajor;
  (void)yyminor;
#define TOKEN (yyminor.yy0)
#line 1579 "queryparser/queryparser.lemony"

    yy_parse_failed(yypParser);
#line 2835 "queryparser/queryparser_internal.cc"
  ParseARG_STORE; /* Suppress warning about unused %extra_argument variable */
}

/*
** The following is executed when the parser accepts
*/
static void yy_accept(
  yyParser *yypParser           /* The parser */
){
  ParseARG_FETCH;
  LOGLINE(QUERYPARSER, "Accept!");
  while( !yypParser->yystack.empty() ) yy_pop_parser_stack(yypParser);
  /* Here code is inserted which will be executed whenever the
  ** parser accepts */
  ParseARG_STORE; /* Suppress warning about unused %extra_argument variable */
}

/* The main parser program.
** The first argument is a pointer to a structure obtained from
** "ParseAlloc" which describes the current state of the parser.
** The second argument is the major token number.  The third is
** the minor token.  The fourth optional argument is whatever the
** user wants (and specified in the grammar) and is available for
** use by the action routines.
**
** Inputs:
** <ul>
** <li> A pointer to the parser (an opaque structure.)
** <li> The major token number.
** <li> The minor token number.
** <li> An option argument of a grammar-specified type.
** </ul>
**
** Outputs:
** None.
*/
static void Parse(
  yyParser *yypParser,         /* The parser */
  int yymajor,                 /* The major token code number */
  ParseTOKENTYPE yyminor       /* The value for the token */
  ParseARG_PDECL               /* Optional %extra_argument parameter */
){
  YYMINORTYPE yyminorunion;
  int yyact;            /* The parser action. */
  int yyendofinput;     /* True if we are at the end of input */
#ifdef YYERRORSYMBOL
  int yyerrorhit = 0;   /* True if yymajor has invoked an error */
#endif

  /* (re)initialize the parser, if necessary */
  if( yypParser->yystack.empty() ){
    yypParser->yystack.push_back(yyStackEntry());
    yypParser->yyerrcnt = -1;
  }
  yyminorunion.yy0 = yyminor;
  yyendofinput = (yymajor==0);
  ParseARG_STORE;

  LOGLINE(QUERYPARSER, "Input " << ParseTokenName(yymajor) << " " <<
	  (yyminor ? yyminor->name : "<<null>>"));

  do{
    yyact = yy_find_shift_action(yypParser,(YYCODETYPE)yymajor);
    if( yyact<YYNSTATE ){
      Assert( !yyendofinput );  /* Impossible to shift the $ token */
      yy_shift(yypParser,yyact,yymajor,&yyminorunion);
      yypParser->yyerrcnt--;
      yymajor = YYNOCODE;
    }else if( yyact < YYNSTATE + YYNRULE ){
      yy_reduce(yypParser,yyact-YYNSTATE);
    }else{
      Assert( yyact == YY_ERROR_ACTION );
#ifdef YYERRORSYMBOL
      int yymx;
#endif
      LOGLINE(QUERYPARSER, "Syntax Error!");
#ifdef YYERRORSYMBOL
      /* A syntax error has occurred.
      ** The response to an error depends upon whether or not the
      ** grammar defines an error token "ERROR".  
      **
      ** This is what we do if the grammar does define ERROR:
      **
      **  * Call the %syntax_error function.
      **
      **  * Begin popping the stack until we enter a state where
      **    it is legal to shift the error symbol, then shift
      **    the error symbol.
      **
      **  * Set the error count to three.
      **
      **  * Begin accepting and shifting new tokens.  No new error
      **    processing will occur until three tokens have been
      **    shifted successfully.
      **
      */
      if( yypParser->yyerrcnt<0 ){
        yy_syntax_error(yypParser,yymajor,yyminorunion);
      }
      yymx = yypParser->yystack.back().major;
      if( yymx==YYERRORSYMBOL || yyerrorhit ){
	LOGLINE(QUERYPARSER, "Discard input token " << ParseTokenName(yymajor));
        yy_destructor(yypParser, (YYCODETYPE)yymajor,&yyminorunion);
        yymajor = YYNOCODE;
      }else{
         while(
          !yypParser->yystack.empty() &&
          yymx != YYERRORSYMBOL &&
          (yyact = yy_find_reduce_action(
                        yypParser->yystack.back().stateno,
                        YYERRORSYMBOL)) >= YYNSTATE
        ){
          yy_pop_parser_stack(yypParser);
        }
        if( yypParser->yystack.empty() || yymajor==0 ){
          yy_destructor(yypParser, (YYCODETYPE)yymajor,&yyminorunion);
          yy_parse_failed(yypParser);
          yymajor = YYNOCODE;
        }else if( yymx!=YYERRORSYMBOL ){
          YYMINORTYPE u2;
          u2.YYERRSYMDT = 0;
          yy_shift(yypParser,yyact,YYERRORSYMBOL,&u2);
        }
      }
      yypParser->yyerrcnt = 3;
      yyerrorhit = 1;
#elif defined(YYNOERRORRECOVERY)
      /* If the YYNOERRORRECOVERY macro is defined, then do not attempt to
      ** do any kind of error recovery.  Instead, simply invoke the syntax
      ** error routine and continue going as if nothing had happened.
      **
      ** Applications can set this macro (for example inside %include) if
      ** they intend to abandon the parse upon the first syntax error seen.
      */
      yy_syntax_error(yypParser,yymajor,yyminorunion);
      yy_destructor(yypParser,(YYCODETYPE)yymajor,&yyminorunion);
      yymajor = YYNOCODE;
      
#else  /* YYERRORSYMBOL is not defined */
      /* This is what we do if the grammar does not define ERROR:
      **
      **  * Report an error message, and throw away the input token.
      **
      **  * If the input token is $, then fail the parse.
      **
      ** As before, subsequent error messages are suppressed until
      ** three input tokens have been successfully shifted.
      */
      if( yypParser->yyerrcnt<=0 ){
        yy_syntax_error(yypParser,yymajor,yyminorunion);
      }
      yypParser->yyerrcnt = 3;
      yy_destructor(yypParser,(YYCODETYPE)yymajor,&yyminorunion);
      if( yyendofinput ){
        yy_parse_failed(yypParser);
      }
      yymajor = YYNOCODE;
#endif
    }
  }while( yymajor!=YYNOCODE && !yypParser->yystack.empty() );
  return;
}

// Select C++ syntax highlighting in vim editor: vim: syntax=cpp
