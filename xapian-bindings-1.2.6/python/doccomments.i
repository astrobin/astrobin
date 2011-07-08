
// File: index.xml

// File: classstd_1_1allocator.xml
%feature("docstring") std::allocator "

STL class. ";


// File: classXapian_1_1AssertionError.xml
%feature("docstring") Xapian::AssertionError "

AssertionError is thrown if a logical assertion inside Xapian fails.

In a debug build of Xapian, a failed assertion in the core library
code will cause AssertionError to be thrown.

This represents a bug in Xapian (either an invariant, precondition,
etc has been violated, or the assertion is incorrect!) ";

%feature("docstring")  Xapian::AssertionError::AssertionError "

General purpose constructor which allows setting errno.

Xapian::AssertionError::AssertionError(const std::string &msg_, const
std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")  Xapian::AssertionError::AssertionError "

Construct from message and errno value.

Xapian::AssertionError::AssertionError(const std::string &msg_, int
errno_) ";


// File: classstd_1_1auto__ptr.xml
%feature("docstring") std::auto_ptr "

STL class. ";


// File: classstd_1_1bad__alloc.xml
%feature("docstring") std::bad_alloc "

STL class. ";


// File: classstd_1_1bad__cast.xml
%feature("docstring") std::bad_cast "

STL class. ";


// File: classstd_1_1bad__exception.xml
%feature("docstring") std::bad_exception "

STL class. ";


// File: classstd_1_1bad__typeid.xml
%feature("docstring") std::bad_typeid "

STL class. ";


// File: classstd_1_1basic__fstream.xml
%feature("docstring") std::basic_fstream "

STL class. ";


// File: classstd_1_1basic__ifstream.xml
%feature("docstring") std::basic_ifstream "

STL class. ";


// File: classstd_1_1basic__ios.xml
%feature("docstring") std::basic_ios "

STL class. ";


// File: classstd_1_1basic__iostream.xml
%feature("docstring") std::basic_iostream "

STL class. ";


// File: classstd_1_1basic__istream.xml
%feature("docstring") std::basic_istream "

STL class. ";


// File: classstd_1_1basic__istringstream.xml
%feature("docstring") std::basic_istringstream "

STL class. ";


// File: classstd_1_1basic__ofstream.xml
%feature("docstring") std::basic_ofstream "

STL class. ";


// File: classstd_1_1basic__ostream.xml
%feature("docstring") std::basic_ostream "

STL class. ";


// File: classstd_1_1basic__ostringstream.xml
%feature("docstring") std::basic_ostringstream "

STL class. ";


// File: classstd_1_1basic__string.xml
%feature("docstring") std::basic_string "

STL class. ";


// File: classstd_1_1basic__stringstream.xml
%feature("docstring") std::basic_stringstream "

STL class. ";


// File: classstd_1_1bitset.xml
%feature("docstring") std::bitset "

STL class. ";


// File: classXapian_1_1BM25Weight.xml
%feature("docstring") Xapian::BM25Weight "

Xapian::Weight subclass implementing the BM25 probabilistic formula.
";

%feature("docstring")  Xapian::BM25Weight::BM25Weight "

Construct a BM25Weight.

Xapian::BM25Weight::BM25Weight(double k1, double k2, double k3, double
b, double min_normlen)

Parameters:
-----------

k1:  A non-negative parameter controlling how influential within-
document- frequency (wdf) is. k1=0 means that wdf doesn't affect the
weights. The larger k1 is, the more wdf influences the weights.
(default 1)

k2:  A non-negative parameter which controls the strength of a
correction factor which depends upon query length and normalised
document length. k2=0 disable this factor; larger k2 makes it
stronger. (default 0)

k3:  A non-negative parameter controlling how influential within-
query- frequency (wqf) is. k3=0 means that wqf doesn't affect the
weights. The larger k3 is, the more wqf influences the weights.
(default 1)

b:  A parameter between 0 and 1, controlling how strong the document
length normalisation of wdf is. 0 means no normalisation; 1 means full
normalisation. (default 0.5)

min_normlen:  A parameter specifying a minimum value for normalised
document length. Normalised document length values less than this will
be clamped to this value, helping to prevent very short documents
getting large weights. (default 0.5) ";

%feature("docstring")  Xapian::BM25Weight::BM25Weight "Xapian::BM25Weight::BM25Weight() ";

%feature("docstring")  Xapian::BM25Weight::name "

Return the name of this weighting scheme.

std::string Xapian::BM25Weight::name() const

This name is used by the remote backend. It is passed along with the
serialised parameters to the remote server so that it knows which
class to create.

Return the full namespace-qualified name of your class here - if your
class is called FooWeight, return \"FooWeight\" from this method (
Xapian::BM25Weight returns \"Xapian::BM25Weight\" here).

If you don't want to support the remote backend, you can use the
default implementation which simply returns an empty string. ";

%feature("docstring")  Xapian::BM25Weight::serialise "

Return this object's parameters serialised as a single string.

std::string Xapian::BM25Weight::serialise() const

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.
";

%feature("docstring")  Xapian::BM25Weight::unserialise "

Unserialise parameters.

BM25Weight* Xapian::BM25Weight::unserialise(const std::string &s)
const

This method unserialises parameters serialised by the  serialise()
method and allocates and returns a new object initialised with them.

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".
";

%feature("docstring")  Xapian::BM25Weight::get_sumpart "

Calculate the weight contribution for this object's term to a
document.

Xapian::weight Xapian::BM25Weight::get_sumpart(Xapian::termcount wdf,
Xapian::termcount doclen) const

The parameters give information about the document which may be used
in the calculations:

Parameters:
-----------

wdf:  The within document frequency of the term in the document.

doclen:  The document's length (unnormalised). ";

%feature("docstring")  Xapian::BM25Weight::get_maxpart "

Return an upper bound on what get_sumpart() can return for any
document.

Xapian::weight Xapian::BM25Weight::get_maxpart() const

This information is used by the matcher to perform various
optimisations, so strive to make the bound as tight as possible. ";

%feature("docstring")  Xapian::BM25Weight::get_sumextra "

Calculate the term-independent weight component for a document.

Xapian::weight Xapian::BM25Weight::get_sumextra(Xapian::termcount
doclen) const

The parameter gives information about the document which may be used
in the calculations:

Parameters:
-----------

doclen:  The document's length (unnormalised). ";

%feature("docstring")  Xapian::BM25Weight::get_maxextra "

Return an upper bound on what get_sumextra() can return for any
document.

Xapian::weight Xapian::BM25Weight::get_maxextra() const

This information is used by the matcher to perform various
optimisations, so strive to make the bound as tight as possible. ";


// File: classXapian_1_1BoolWeight.xml
%feature("docstring") Xapian::BoolWeight "

Class implementing a \"boolean\" weighting scheme.

This weighting scheme gives all documents zero weight. ";

%feature("docstring")  Xapian::BoolWeight::BoolWeight "

Construct a BoolWeight.

Xapian::BoolWeight::BoolWeight() ";

%feature("docstring")  Xapian::BoolWeight::name "

Return the name of this weighting scheme.

std::string Xapian::BoolWeight::name() const

This name is used by the remote backend. It is passed along with the
serialised parameters to the remote server so that it knows which
class to create.

Return the full namespace-qualified name of your class here - if your
class is called FooWeight, return \"FooWeight\" from this method (
Xapian::BM25Weight returns \"Xapian::BM25Weight\" here).

If you don't want to support the remote backend, you can use the
default implementation which simply returns an empty string. ";

%feature("docstring")  Xapian::BoolWeight::serialise "

Return this object's parameters serialised as a single string.

std::string Xapian::BoolWeight::serialise() const

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.
";

%feature("docstring")  Xapian::BoolWeight::unserialise "

Unserialise parameters.

BoolWeight* Xapian::BoolWeight::unserialise(const std::string &s)
const

This method unserialises parameters serialised by the  serialise()
method and allocates and returns a new object initialised with them.

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".
";

%feature("docstring")  Xapian::BoolWeight::get_sumpart "

Calculate the weight contribution for this object's term to a
document.

Xapian::weight Xapian::BoolWeight::get_sumpart(Xapian::termcount wdf,
Xapian::termcount doclen) const

The parameters give information about the document which may be used
in the calculations:

Parameters:
-----------

wdf:  The within document frequency of the term in the document.

doclen:  The document's length (unnormalised). ";

%feature("docstring")  Xapian::BoolWeight::get_maxpart "

Return an upper bound on what get_sumpart() can return for any
document.

Xapian::weight Xapian::BoolWeight::get_maxpart() const

This information is used by the matcher to perform various
optimisations, so strive to make the bound as tight as possible. ";

%feature("docstring")  Xapian::BoolWeight::get_sumextra "

Calculate the term-independent weight component for a document.

Xapian::weight Xapian::BoolWeight::get_sumextra(Xapian::termcount
doclen) const

The parameter gives information about the document which may be used
in the calculations:

Parameters:
-----------

doclen:  The document's length (unnormalised). ";

%feature("docstring")  Xapian::BoolWeight::get_maxextra "

Return an upper bound on what get_sumextra() can return for any
document.

Xapian::weight Xapian::BoolWeight::get_maxextra() const

This information is used by the matcher to perform various
optimisations, so strive to make the bound as tight as possible. ";


// File: classXapian_1_1Compactor.xml
%feature("docstring") Xapian::Compactor "

Compact a database, or merge and compact several. ";

%feature("docstring")  Xapian::Compactor::Compactor "Xapian::Compactor::Compactor() ";

%feature("docstring")  Xapian::Compactor::~Compactor "virtual
Xapian::Compactor::~Compactor() ";

%feature("docstring")  Xapian::Compactor::set_block_size "

Set the block size to use for tables in the output database.

void Xapian::Compactor::set_block_size(size_t block_size)

Valid block sizes are currently powers of two between 2048 and 65536,
with the default being 8192, but the valid sizes and default may
change in the future. ";

%feature("docstring")  Xapian::Compactor::set_renumber "

Set whether to preserve existing document id values.

void Xapian::Compactor::set_renumber(bool renumber)

The default is true, which means that document ids will be renumbered
- currently by applying the same offset to all the document ids in a
particular source database.

If false, then the document ids must be unique over all source
databases. Currently the ranges of document ids in each source must
not overlap either, though this restriction may be removed in the
future. ";

%feature("docstring")  Xapian::Compactor::set_multipass "

Set whether to merge postlists in multiple passes.

void Xapian::Compactor::set_multipass(bool multipass)

Default is false. If set to true and merging more than 3 databases,
merge the postlists in multiple passes, which is generally faster but
requires more disk space for temporary files. ";

%feature("docstring")  Xapian::Compactor::set_compaction_level "

Set the compaction level.

void Xapian::Compactor::set_compaction_level(compaction_level
compaction)

Values are: Xapian::Compactor::STANDARD - Don't split items
unnecessarily.

Xapian::Compactor::FULL - Split items whenever it saves space (the
default).

Xapian::Compactor::FULLER - Allow oversize items to save more space.

FULLER isn't recommended if you ever plan to update the compacted
database. ";

%feature("docstring")  Xapian::Compactor::set_destdir "

Set where to write the output.

void Xapian::Compactor::set_destdir(const std::string &destdir)

This can be the same as an input if that input is a stub database (in
which case it will be updated atomically). ";

%feature("docstring")  Xapian::Compactor::add_source "

Add a source database.

void Xapian::Compactor::add_source(const std::string &srcdir) ";

%feature("docstring")  Xapian::Compactor::compact "

Perform the actual compaction/merging operation.

void Xapian::Compactor::compact() ";

%feature("docstring")  Xapian::Compactor::set_status "

Update progress.

virtual void Xapian::Compactor::set_status(const std::string &table,
const std::string &status)

Subclass this method if you want to get progress updates during
compaction. This is called for each table first with empty status, And
then one or more times with non-empty status.

The default implementation does nothing. ";

%feature("docstring")  Xapian::Compactor::resolve_duplicate_metadata "

Resolve multiple user metadata entries with the same key.

virtual std::string
Xapian::Compactor::resolve_duplicate_metadata(const std::string &key,
size_t num_tags, const std::string tags[])

When merging, if the same user metadata key is set in more than one
input, then this method is called to allow this to be resolving in an
appropriate way.

The default implementation just returns tags[0].

For multipass this will currently get called multiple times for the
same key if there are duplicates to resolve in each pass, but this may
change in the future. ";


// File: classstd_1_1complex.xml
%feature("docstring") std::complex "

STL class. ";


// File: classstd_1_1list_1_1const__iterator.xml
%feature("docstring") std::list::const_iterator "

STL iterator class. ";


// File: classstd_1_1map_1_1const__iterator.xml
%feature("docstring") std::map::const_iterator "

STL iterator class. ";


// File: classstd_1_1multimap_1_1const__iterator.xml
%feature("docstring") std::multimap::const_iterator "

STL iterator class. ";


// File: classstd_1_1set_1_1const__iterator.xml
%feature("docstring") std::set::const_iterator "

STL iterator class. ";


// File: classstd_1_1multiset_1_1const__iterator.xml
%feature("docstring") std::multiset::const_iterator "

STL iterator class. ";


// File: classstd_1_1vector_1_1const__iterator.xml
%feature("docstring") std::vector::const_iterator "

STL iterator class. ";


// File: classstd_1_1basic__string_1_1const__iterator.xml
%feature("docstring") std::basic_string::const_iterator "

STL iterator class. ";


// File: classstd_1_1wstring_1_1const__iterator.xml
%feature("docstring") std::wstring::const_iterator "

STL iterator class. ";


// File: classstd_1_1string_1_1const__iterator.xml
%feature("docstring") std::string::const_iterator "

STL iterator class. ";


// File: classstd_1_1deque_1_1const__iterator.xml
%feature("docstring") std::deque::const_iterator "

STL iterator class. ";


// File: classstd_1_1list_1_1const__reverse__iterator.xml
%feature("docstring") std::list::const_reverse_iterator "

STL iterator class. ";


// File: classstd_1_1map_1_1const__reverse__iterator.xml
%feature("docstring") std::map::const_reverse_iterator "

STL iterator class. ";


// File: classstd_1_1multimap_1_1const__reverse__iterator.xml
%feature("docstring") std::multimap::const_reverse_iterator "

STL iterator class. ";


// File: classstd_1_1set_1_1const__reverse__iterator.xml
%feature("docstring") std::set::const_reverse_iterator "

STL iterator class. ";


// File: classstd_1_1multiset_1_1const__reverse__iterator.xml
%feature("docstring") std::multiset::const_reverse_iterator "

STL iterator class. ";


// File: classstd_1_1vector_1_1const__reverse__iterator.xml
%feature("docstring") std::vector::const_reverse_iterator "

STL iterator class. ";


// File: classstd_1_1basic__string_1_1const__reverse__iterator.xml
%feature("docstring") std::basic_string::const_reverse_iterator "

STL iterator class. ";


// File: classstd_1_1string_1_1const__reverse__iterator.xml
%feature("docstring") std::string::const_reverse_iterator "

STL iterator class. ";


// File: classstd_1_1wstring_1_1const__reverse__iterator.xml
%feature("docstring") std::wstring::const_reverse_iterator "

STL iterator class. ";


// File: classstd_1_1deque_1_1const__reverse__iterator.xml
%feature("docstring") std::deque::const_reverse_iterator "

STL iterator class. ";


// File: classXapian_1_1Database.xml
%feature("docstring") Xapian::Database "

This class is used to access a database, or a group of databases.

For searching, this class is used in conjunction with an Enquire
object.

Parameters:
-----------

InvalidArgumentError:  will be thrown if an invalid argument is
supplied, for example, an unknown database type.

DatabaseOpeningError:  may be thrown if the database cannot be opened
(for example, a required file cannot be found).

DatabaseVersionError:  may be thrown if the database is in an
unsupported format (for example, created by a newer version of Xapian
which uses an incompatible format). ";

%feature("docstring")  Xapian::Database::add_database "

Add an existing database (or group of databases) to those accessed by
this object.

void Xapian::Database::add_database(const Database &database)

Parameters:
-----------

database:  the database(s) to add. ";

%feature("docstring")  Xapian::Database::Database "

Create a Database with no databases in.

Xapian::Database::Database() ";

%feature("docstring")  Xapian::Database::Database "

Open a Database, automatically determining the database backend to
use.

Xapian::Database::Database(const std::string &path)

Parameters:
-----------

path:  directory that the database is stored in. ";

%feature("docstring")  Xapian::Database::~Database "

Destroy this handle on the database.

virtual Xapian::Database::~Database()

If there are no copies of this object remaining, the database(s) will
be closed. ";

%feature("docstring")  Xapian::Database::Database "

Copying is allowed.

Xapian::Database::Database(const Database &other)

The internals are reference counted, so copying is cheap. ";

%feature("docstring")  Xapian::Database::reopen "

Re-open the database.

void Xapian::Database::reopen()

This re-opens the database(s) to the latest available version(s). It
can be used either to make sure the latest results are returned, or to
recover from a Xapian::DatabaseModifiedError.

Calling reopen() on a database which has been closed (with  close())
will always raise a Xapian::DatabaseError. ";

%feature("docstring")  Xapian::Database::close "

Close the database.

virtual void Xapian::Database::close()

This closes the database and releases all file handles held by the
database.

This is a permanent close of the database: calling reopen() after
closing a database will not reopen it, and will raise an exception.

Calling close() on a database which is already closed has no effect
(and doesn't raise an exception).

After this call, calls made to methods of the database (other than
close() or the destructor), or to objects associated with the database
will behave in one of the following ways (but which behaviour happens
may vary between releases, and between database backends):

raise a Xapian::DatabaseError indicating that the database is closed.

behave exactly as they would have done if the database had not been
closed (by using cached data).

To summarise - you should not rely on the exception being raised, or
the normal result being available, but if you do get a result, it will
be correct. ";

%feature("docstring")  Xapian::Database::get_description "

Return a string describing this object.

virtual std::string Xapian::Database::get_description() const ";

%feature("docstring")  Xapian::Database::postlist_begin "

An iterator pointing to the start of the postlist for a given term.

PostingIterator Xapian::Database::postlist_begin(const std::string
&tname) const

If the term name is the empty string, the iterator returned will list
all the documents in the database. Such an iterator will always return
a WDF value of 1, since there is no obvious meaning for this quantity
in this case. ";

%feature("docstring")  Xapian::Database::postlist_end "

Corresponding end iterator to postlist_begin().

PostingIterator Xapian::Database::postlist_end(const std::string &)
const ";

%feature("docstring")  Xapian::Database::termlist_begin "

An iterator pointing to the start of the termlist for a given
document.

TermIterator Xapian::Database::termlist_begin(Xapian::docid did) const
";

%feature("docstring")  Xapian::Database::termlist_end "

Corresponding end iterator to termlist_begin().

TermIterator Xapian::Database::termlist_end(Xapian::docid) const ";

%feature("docstring")  Xapian::Database::has_positions "

Does this database have any positional information?

bool Xapian::Database::has_positions() const ";

%feature("docstring")  Xapian::Database::positionlist_begin "

An iterator pointing to the start of the position list for a given
term in a given document.

PositionIterator Xapian::Database::positionlist_begin(Xapian::docid
did, const std::string &tname) const ";

%feature("docstring")  Xapian::Database::positionlist_end "

Corresponding end iterator to positionlist_begin().

PositionIterator Xapian::Database::positionlist_end(Xapian::docid,
const std::string &) const ";

%feature("docstring")  Xapian::Database::allterms_begin "

An iterator which runs across all terms in the database.

TermIterator Xapian::Database::allterms_begin() const ";

%feature("docstring")  Xapian::Database::allterms_end "

Corresponding end iterator to allterms_begin().

TermIterator Xapian::Database::allterms_end() const ";

%feature("docstring")  Xapian::Database::allterms_begin "

An iterator which runs across all terms with a given prefix.

TermIterator Xapian::Database::allterms_begin(const std::string
&prefix) const

This is functionally similar to getting an iterator with
allterms_begin() and then calling skip_to(prefix) on that iterator to
move to the start of the prefix, but is more convenient (because it
detects the end of the prefixed terms), and may be more efficient than
simply calling skip_to() after opening the iterator, particularly for
remote databases.

Parameters:
-----------

prefix:  The prefix to restrict the returned terms to. ";

%feature("docstring")  Xapian::Database::allterms_end "

Corresponding end iterator to allterms_begin(prefix).

TermIterator Xapian::Database::allterms_end(const std::string &) const
";

%feature("docstring")  Xapian::Database::get_doccount "

Get the number of documents in the database.

Xapian::doccount Xapian::Database::get_doccount() const ";

%feature("docstring")  Xapian::Database::get_lastdocid "

Get the highest document id which has been used in the database.

Xapian::docid Xapian::Database::get_lastdocid() const ";

%feature("docstring")  Xapian::Database::get_avlength "

Get the average length of the documents in the database.

Xapian::doclength Xapian::Database::get_avlength() const ";

%feature("docstring")  Xapian::Database::get_termfreq "

Get the number of documents in the database indexed by a given term.

Xapian::doccount Xapian::Database::get_termfreq(const std::string
&tname) const ";

%feature("docstring")  Xapian::Database::term_exists "

Check if a given term exists in the database.

bool Xapian::Database::term_exists(const std::string &tname) const

Return true if and only if the term exists in the database. This is
the same as (get_termfreq(tname) != 0), but will often be more
efficient. ";

%feature("docstring")  Xapian::Database::get_collection_freq "

Return the total number of occurrences of the given term.

Xapian::termcount Xapian::Database::get_collection_freq(const
std::string &tname) const

This is the sum of the number of occurrences of the term in each
document it indexes: i.e., the sum of the within document frequencies
of the term.

Parameters:
-----------

tname:  The term whose collection frequency is being requested. ";

%feature("docstring")  Xapian::Database::get_value_freq "

Return the frequency of a given value slot.

Xapian::doccount Xapian::Database::get_value_freq(Xapian::valueno
slot) const

This is the number of documents which have a (non-empty) value stored
in the slot.

Parameters:
-----------

slot:  The value slot to examine.

Parameters:
-----------

UnimplementedError:  The frequency of the value isn't available for
this database type. ";

%feature("docstring")  Xapian::Database::get_value_lower_bound "

Get a lower bound on the values stored in the given value slot.

std::string Xapian::Database::get_value_lower_bound(Xapian::valueno
slot) const

If there are no values stored in the given value slot, this will
return an empty string.

If the lower bound isn't available for the given database type, this
will return the lowest possible bound - the empty string.

Parameters:
-----------

slot:  The value slot to examine. ";

%feature("docstring")  Xapian::Database::get_value_upper_bound "

Get an upper bound on the values stored in the given value slot.

std::string Xapian::Database::get_value_upper_bound(Xapian::valueno
slot) const

If there are no values stored in the given value slot, this will
return an empty string.

Parameters:
-----------

slot:  The value slot to examine.

Parameters:
-----------

UnimplementedError:  The upper bound of the values isn't available for
this database type. ";

%feature("docstring")  Xapian::Database::get_doclength_lower_bound "

Get a lower bound on the length of a document in this DB.

Xapian::termcount Xapian::Database::get_doclength_lower_bound() const

This bound does not include any zero-length documents. ";

%feature("docstring")  Xapian::Database::get_doclength_upper_bound "

Get an upper bound on the length of a document in this DB.

Xapian::termcount Xapian::Database::get_doclength_upper_bound() const
";

%feature("docstring")  Xapian::Database::get_wdf_upper_bound "

Get an upper bound on the wdf of term term.

Xapian::termcount Xapian::Database::get_wdf_upper_bound(const
std::string &term) const ";

%feature("docstring")  Xapian::Database::valuestream_begin "

Return an iterator over the value in slot slot for each document.

ValueIterator Xapian::Database::valuestream_begin(Xapian::valueno
slot) const ";

%feature("docstring")  Xapian::Database::valuestream_end "

Return end iterator corresponding to valuestream_begin().

ValueIteratorEnd_ Xapian::Database::valuestream_end(Xapian::valueno)
const ";

%feature("docstring")  Xapian::Database::get_doclength "

Get the length of a document.

Xapian::termcount Xapian::Database::get_doclength(Xapian::docid did)
const ";

%feature("docstring")  Xapian::Database::keep_alive "

Send a \"keep-alive\" to remote databases to stop them timing out.

void Xapian::Database::keep_alive()

Has no effect on non-remote databases. ";

%feature("docstring")  Xapian::Database::get_document "

Get a document from the database, given its document id.

Xapian::Document Xapian::Database::get_document(Xapian::docid did)
const

This method returns a Xapian::Document object which provides the
information about a document.

Parameters:
-----------

did:  The document id of the document to retrieve.

A Xapian::Document object containing the document data

Parameters:
-----------

Xapian::DocNotFoundError:  The document specified could not be found
in the database.

Xapian::InvalidArgumentError:  did was 0, which is not a valid
document id. ";

%feature("docstring")  Xapian::Database::get_spelling_suggestion "

Suggest a spelling correction.

std::string Xapian::Database::get_spelling_suggestion(const
std::string &word, unsigned max_edit_distance=2) const

Parameters:
-----------

word:  The potentially misspelled word.

max_edit_distance:  Only consider words which are at most
max_edit_distance edits from word. An edit is a character insertion,
deletion, or the transposition of two adjacent characters (default is
2). ";

%feature("docstring")  Xapian::Database::spellings_begin "

An iterator which returns all the spelling correction targets.

Xapian::TermIterator Xapian::Database::spellings_begin() const

This returns all the words which are considered as targets for the
spelling correction algorithm. The frequency of each word is available
as the term frequency of each entry in the returned iterator. ";

%feature("docstring")  Xapian::Database::spellings_end "

Corresponding end iterator to spellings_begin().

Xapian::TermIterator Xapian::Database::spellings_end() const ";

%feature("docstring")  Xapian::Database::synonyms_begin "

An iterator which returns all the synonyms for a given term.

Xapian::TermIterator Xapian::Database::synonyms_begin(const
std::string &term) const

Parameters:
-----------

term:  The term to return synonyms for. ";

%feature("docstring")  Xapian::Database::synonyms_end "

Corresponding end iterator to synonyms_begin(term).

Xapian::TermIterator Xapian::Database::synonyms_end(const std::string
&) const ";

%feature("docstring")  Xapian::Database::synonym_keys_begin "

An iterator which returns all terms which have synonyms.

Xapian::TermIterator Xapian::Database::synonym_keys_begin(const
std::string &prefix=std::string()) const

Parameters:
-----------

prefix:  If non-empty, only terms with this prefix are returned. ";

%feature("docstring")  Xapian::Database::synonym_keys_end "

Corresponding end iterator to synonym_keys_begin(prefix).

Xapian::TermIterator Xapian::Database::synonym_keys_end(const
std::string &=std::string()) const ";

%feature("docstring")  Xapian::Database::get_metadata "

Get the user-specified metadata associated with a given key.

std::string Xapian::Database::get_metadata(const std::string &key)
const

User-specified metadata allows you to store arbitrary information in
the form of (key,tag) pairs. See  WritableDatabase::set_metadata() for
more information.

When invoked on a Xapian::Database object representing multiple
databases, currently only the metadata for the first is considered but
this behaviour may change in the future.

If there is no piece of metadata associated with the specified key, an
empty string is returned (this applies even for backends which don't
support metadata).

Empty keys are not valid, and specifying one will cause an exception.

Parameters:
-----------

key:  The key of the metadata item to access.

The retrieved metadata item's value.

Parameters:
-----------

Xapian::InvalidArgumentError:  will be thrown if the key supplied is
empty. ";

%feature("docstring")  Xapian::Database::metadata_keys_begin "

An iterator which returns all user-specified metadata keys.

Xapian::TermIterator Xapian::Database::metadata_keys_begin(const
std::string &prefix=std::string()) const

When invoked on a Xapian::Database object representing multiple
databases, currently only the metadata for the first is considered but
this behaviour may change in the future.

If the backend doesn't support metadata, then this method returns an
iterator which compares equal to that returned by metadata_keys_end().

Parameters:
-----------

prefix:  If non-empty, only keys with this prefix are returned.

Parameters:
-----------

Xapian::UnimplementedError:  will be thrown if the backend implements
user-specified metadata, but doesn't implement iterating its keys
(currently this happens for the InMemory backend). ";

%feature("docstring")  Xapian::Database::metadata_keys_end "

Corresponding end iterator to metadata_keys_begin().

Xapian::TermIterator Xapian::Database::metadata_keys_end(const
std::string &=std::string()) const ";

%feature("docstring")  Xapian::Database::get_uuid "

Get a UUID for the database.

std::string Xapian::Database::get_uuid() const

The UUID will persist for the lifetime of the database.

Replicas (eg, made with the replication protocol, or by copying all
the database files) will have the same UUID. However, copies (made
with copydatabase, or xapian-compact) will have different UUIDs.

If the backend does not support UUIDs or this database has no
subdatabases, the UUID will be empty.

If this database has multiple sub-databases, the UUID string will
contain the UUIDs of all the sub-databases. ";


// File: classXapian_1_1DatabaseCorruptError.xml
%feature("docstring") Xapian::DatabaseCorruptError "

DatabaseCorruptError indicates database corruption was detected. ";

%feature("docstring")
Xapian::DatabaseCorruptError::DatabaseCorruptError "

General purpose constructor which allows setting errno.

Xapian::DatabaseCorruptError::DatabaseCorruptError(const std::string
&msg_, const std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")
Xapian::DatabaseCorruptError::DatabaseCorruptError "

Construct from message and errno value.

Xapian::DatabaseCorruptError::DatabaseCorruptError(const std::string
&msg_, int errno_) ";


// File: classXapian_1_1DatabaseCreateError.xml
%feature("docstring") Xapian::DatabaseCreateError "

DatabaseCreateError indicates a failure to create a database. ";

%feature("docstring")
Xapian::DatabaseCreateError::DatabaseCreateError "

General purpose constructor which allows setting errno.

Xapian::DatabaseCreateError::DatabaseCreateError(const std::string
&msg_, const std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")
Xapian::DatabaseCreateError::DatabaseCreateError "

Construct from message and errno value.

Xapian::DatabaseCreateError::DatabaseCreateError(const std::string
&msg_, int errno_) ";


// File: classXapian_1_1DatabaseError.xml
%feature("docstring") Xapian::DatabaseError "

DatabaseError indicates some sort of database related error. ";

%feature("docstring")  Xapian::DatabaseError::DatabaseError "

General purpose constructor which allows setting errno.

Xapian::DatabaseError::DatabaseError(const std::string &msg_, const
std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")  Xapian::DatabaseError::DatabaseError "

Construct from message and errno value.

Xapian::DatabaseError::DatabaseError(const std::string &msg_, int
errno_) ";


// File: classXapian_1_1DatabaseLockError.xml
%feature("docstring") Xapian::DatabaseLockError "

DatabaseLockError indicates failure to lock a database. ";

%feature("docstring")  Xapian::DatabaseLockError::DatabaseLockError "

General purpose constructor which allows setting errno.

Xapian::DatabaseLockError::DatabaseLockError(const std::string &msg_,
const std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")  Xapian::DatabaseLockError::DatabaseLockError "

Construct from message and errno value.

Xapian::DatabaseLockError::DatabaseLockError(const std::string &msg_,
int errno_) ";


// File: classXapian_1_1DatabaseModifiedError.xml
%feature("docstring") Xapian::DatabaseModifiedError "

DatabaseModifiedError indicates a database was modified.

To recover after catching this error, you need to call
Xapian::Database::reopen() on the Database and repeat the operation
which failed. ";

%feature("docstring")
Xapian::DatabaseModifiedError::DatabaseModifiedError "

General purpose constructor which allows setting errno.

Xapian::DatabaseModifiedError::DatabaseModifiedError(const std::string
&msg_, const std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")
Xapian::DatabaseModifiedError::DatabaseModifiedError "

Construct from message and errno value.

Xapian::DatabaseModifiedError::DatabaseModifiedError(const std::string
&msg_, int errno_) ";


// File: classXapian_1_1DatabaseOpeningError.xml
%feature("docstring") Xapian::DatabaseOpeningError "

DatabaseOpeningError indicates failure to open a database. ";

%feature("docstring")
Xapian::DatabaseOpeningError::DatabaseOpeningError "

General purpose constructor which allows setting errno.

Xapian::DatabaseOpeningError::DatabaseOpeningError(const std::string
&msg_, const std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")
Xapian::DatabaseOpeningError::DatabaseOpeningError "

Construct from message and errno value.

Xapian::DatabaseOpeningError::DatabaseOpeningError(const std::string
&msg_, int errno_) ";


// File: classXapian_1_1DatabaseVersionError.xml
%feature("docstring") Xapian::DatabaseVersionError "

DatabaseVersionError indicates that a database is in an unsupported
format.

From time to time, new versions of Xapian will require the database
format to be changed, to allow new information to be stored or new
optimisations to be performed. Backwards compatibility will sometimes
be maintained, so that new versions of Xapian can open old databases,
but in some cases Xapian will be unable to open a database because it
is in too old (or new) a format. This can be resolved either be
upgrading or downgrading the version of Xapian in use, or by
rebuilding the database from scratch with the current version of
Xapian. ";

%feature("docstring")
Xapian::DatabaseVersionError::DatabaseVersionError "

General purpose constructor which allows setting errno.

Xapian::DatabaseVersionError::DatabaseVersionError(const std::string
&msg_, const std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")
Xapian::DatabaseVersionError::DatabaseVersionError "

Construct from message and errno value.

Xapian::DatabaseVersionError::DatabaseVersionError(const std::string
&msg_, int errno_) ";


// File: classXapian_1_1DateValueRangeProcessor.xml
%feature("docstring") Xapian::DateValueRangeProcessor "

Handle a date range.

Begin and end must be dates in a recognised format. ";

%feature("docstring")
Xapian::DateValueRangeProcessor::DateValueRangeProcessor "

Constructor.

Xapian::DateValueRangeProcessor::DateValueRangeProcessor(Xapian::valueno
slot_, bool prefer_mdy_=false, int epoch_year_=1970)

Parameters:
-----------

slot_:  The value number to return from operator().

prefer_mdy_:  Should ambiguous dates be interpreted as month/day/year
rather than day/month/year? (default: false)

epoch_year_:  Year to use as the epoch for dates with 2 digit years
(default: 1970, so 1/1/69 is 2069 while 1/1/70 is 1970). ";

%feature("docstring")
Xapian::DateValueRangeProcessor::DateValueRangeProcessor "

Constructor.

Xapian::DateValueRangeProcessor::DateValueRangeProcessor(Xapian::valueno
slot_, const std::string &str_, bool prefix_=true, bool
prefer_mdy_=false, int epoch_year_=1970)

Parameters:
-----------

slot_:  The value number to return from operator().

str_:  A string to look for to recognise values as belonging to this
date range.

prefix_:  Whether to look for the string at the start or end of the
values. If true, the string is a prefix; if false, the string is a
suffix (default: true).

prefer_mdy_:  Should ambiguous dates be interpreted as month/day/year
rather than day/month/year? (default: false)

epoch_year_:  Year to use as the epoch for dates with 2 digit years
(default: 1970, so 1/1/69 is 2069 while 1/1/70 is 1970).

The string supplied in str_ is used by operator() to decide whether
the pair of strings supplied to it constitute a valid range. If
prefix_ is true, the first value in a range must begin with str_ (and
the second value may optionally begin with str_); if prefix_ is false,
the second value in a range must end with str_ (and the first value
may optionally end with str_).

If str_ is empty, the setting of prefix_ is irrelevant, and no special
strings are required at the start or end of the strings defining the
range.

The remainder of both strings defining the endpoints must be valid
dates.

For example, if str_ is \"created:\" and prefix_ is true, and the
range processor has been added to the queryparser, the queryparser
will accept \"created:1/1/2000..31/12/2001\". ";


// File: classXapian_1_1DecreasingValueWeightPostingSource.xml
%feature("docstring") Xapian::DecreasingValueWeightPostingSource "

Read weights from a value which is known to decrease as docid
increases.

This posting source can be used, like ValueWeightPostingSource, to add
a weight contribution to a query based on the values stored in a slot.
The values in the slot must be serialised as by  sortable_serialise().

However, this posting source is additionally given a range of document
IDs, within which the weight is known to be decreasing. ie, for all
documents with ids A and B within this range (including the
endpoints), where A is less than B, the weight of A is less than or
equal to the weight of B. This can allow the posting source to skip to
the end of the range quickly if insufficient weight is left in the
posting source for a particular source.

By default, the range is assumed to cover all document IDs.

The ordering property can be arranged at index time, or by sorting an
indexed database to produce a new, sorted, database. ";

%feature("docstring")
Xapian::DecreasingValueWeightPostingSource::DecreasingValueWeightPostingSource
"Xapian::DecreasingValueWeightPostingSource::DecreasingValueWeightPostingSource(Xapian::valueno
slot_, Xapian::docid range_start_=0, Xapian::docid range_end_=0) ";

%feature("docstring")
Xapian::DecreasingValueWeightPostingSource::get_weight "

Return the weight contribution for the current document.

Xapian::weight
Xapian::DecreasingValueWeightPostingSource::get_weight() const

This default implementation always returns 0, for convenience when
implementing \"weight-less\" PostingSource subclasses.

This method may assume that it will only be called when there is a
\"current document\". In detail: Xapian will always call init() on a
PostingSource before calling this for the first time. It will also
only call this if the PostingSource reports that it is pointing to a
valid document (ie, it will not call it before calling at least one of
next(), skip_to() or check(), and will ensure that the PostingSource
is not at the end by calling at_end()). ";

%feature("docstring")
Xapian::DecreasingValueWeightPostingSource::clone "

Clone the posting source.

DecreasingValueWeightPostingSource*
Xapian::DecreasingValueWeightPostingSource::clone() const

The clone should inherit the configuration of the parent, but need not
inherit the state. ie, the clone does not need to be in the same
iteration position as the original: the matcher will always call
init() on the clone before attempting to move the iterator, or read
the information about the current position of the iterator.

This may return NULL to indicate that cloning is not supported. In
this case, the PostingSource may only be used with a single-database
search.

The default implementation returns NULL.

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".
";

%feature("docstring")
Xapian::DecreasingValueWeightPostingSource::name "

Name of the posting source class.

std::string Xapian::DecreasingValueWeightPostingSource::name() const

This is used when serialising and unserialising posting sources; for
example, for performing remote searches.

If the subclass is in a C++ namespace, the namespace should be
included in the name, using \"::\" as a separator. For example, for a
PostingSource subclass called \"FooPostingSource\" in the \"Xapian\"
namespace the result of this call should be
\"Xapian::FooPostingSource\".

This should only be implemented if serialise() and unserialise() are
also implemented. The default implementation returns an empty string.

If this returns an empty string, Xapian will assume that serialise()
and unserialise() are not implemented. ";

%feature("docstring")
Xapian::DecreasingValueWeightPostingSource::serialise "

Serialise object parameters into a string.

std::string Xapian::DecreasingValueWeightPostingSource::serialise()
const

The serialised parameters should represent the configuration of the
posting source, but need not (indeed, should not) represent the
current iteration state.

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.
";

%feature("docstring")
Xapian::DecreasingValueWeightPostingSource::unserialise "

Create object given string serialisation returned by serialise().

DecreasingValueWeightPostingSource*
Xapian::DecreasingValueWeightPostingSource::unserialise(const
std::string &s) const

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.

Parameters:
-----------

s:  A serialised instance of this PostingSource subclass. ";

%feature("docstring")
Xapian::DecreasingValueWeightPostingSource::init "

Set this PostingSource to the start of the list of postings.

void Xapian::DecreasingValueWeightPostingSource::init(const
Xapian::Database &db_)

This is called automatically by the matcher prior to each query being
processed.

If a PostingSource is used for multiple searches,  init() will
therefore be called multiple times, and must handle this by using the
database passed in the most recent call.

Parameters:
-----------

db:  The database which the PostingSource should iterate through.

Note: the database supplied to this method must not be modified: in
particular, the reopen() method should not be called on it.

Note: in the case of a multi-database search, a separate PostingSource
will be used for each database (the separate PostingSources will be
obtained using  clone()), and each PostingSource will be passed one of
the sub-databases as the db parameter here. The db parameter will
therefore always refer to a single database. All docids passed to, or
returned from, the PostingSource refer to docids in that single
database, rather than in the multi- database. ";

%feature("docstring")
Xapian::DecreasingValueWeightPostingSource::next "

Advance the current position to the next matching document.

void Xapian::DecreasingValueWeightPostingSource::next(Xapian::weight
min_wt)

The PostingSource starts before the first entry in the list, so next()
must be called before any methods which need the context of the
current position.

Xapian will always call init() on a PostingSource before calling this
for the first time.

Parameters:
-----------

min_wt:  The minimum weight contribution that is needed (this is just
a hint which subclasses may ignore). ";

%feature("docstring")
Xapian::DecreasingValueWeightPostingSource::skip_to "

Advance to the specified docid.

void Xapian::DecreasingValueWeightPostingSource::skip_to(Xapian::docid
min_docid, Xapian::weight min_wt)

If the specified docid isn't in the list, position ourselves on the
first document after it (or at_end() if no greater docids are
present).

If the current position is already the specified docid, this method
will leave the position unmodified.

If the specified docid is earlier than the current position, the
behaviour is unspecified. A sensible behaviour would be to leave the
current position unmodified, but it is also reasonable to move to the
specified docid.

The default implementation calls next() repeatedly, which works but
skip_to() can often be implemented much more efficiently.

Xapian will always call init() on a PostingSource before calling this
for the first time.

Note: in the case of a multi-database search, the docid specified is
the docid in the single subdatabase relevant to this posting source.
See the  init() method for details.

Parameters:
-----------

min_wt:  The minimum weight contribution that is needed (this is just
a hint which subclasses may ignore). ";

%feature("docstring")
Xapian::DecreasingValueWeightPostingSource::check "

Check if the specified docid occurs.

bool Xapian::DecreasingValueWeightPostingSource::check(Xapian::docid
min_docid, Xapian::weight min_wt)

The caller is required to ensure that the specified document id did
actually exists in the database. If it does, it must move to that
document id, and return true. If it does not, it may either:

return true, having moved to a definite position (including
\"at_end\"), which must be the same position as skip_to() would have
moved to.

or

return false, having moved to an \"indeterminate\" position, such that
a subsequent call to next() or skip_to() will move to the next
matching position after did.

Generally, this method should act like skip_to() and return true if
that can be done at little extra cost.

Otherwise it should simply check if a particular docid is present,
returning true if it is, and false if it isn't.

The default implementation calls skip_to() and always returns true.

Xapian will always call init() on a PostingSource before calling this
for the first time.

Note: in the case of a multi-database search, the docid specified is
the docid in the single subdatabase relevant to this posting source.
See the  init() method for details. ";

%feature("docstring")
Xapian::DecreasingValueWeightPostingSource::get_description "

Return a string describing this object.

std::string
Xapian::DecreasingValueWeightPostingSource::get_description() const

This default implementation returns a generic answer. This default it
provided to avoid forcing those deriving their own PostingSource
subclass from having to implement this (they may not care what
get_description() gives for their subclass). ";


// File: classstd_1_1deque.xml
%feature("docstring") std::deque "

STL class. ";


// File: classXapian_1_1DocNotFoundError.xml
%feature("docstring") Xapian::DocNotFoundError "

Indicates an attempt to access a document not present in the database.
";

%feature("docstring")  Xapian::DocNotFoundError::DocNotFoundError "

General purpose constructor which allows setting errno.

Xapian::DocNotFoundError::DocNotFoundError(const std::string &msg_,
const std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")  Xapian::DocNotFoundError::DocNotFoundError "

Construct from message and errno value.

Xapian::DocNotFoundError::DocNotFoundError(const std::string &msg_,
int errno_) ";


// File: classXapian_1_1Document.xml
%feature("docstring") Xapian::Document "

A handle representing a document in a Xapian database.

The Document class fetches information from the database lazily.
Usually this behaviour isn't visible to users (except for the speed
benefits), but if the document in the database is modified or deleted,
then preexisting Document objects may return the old or new versions
of data (or throw Xapian::DocNotFoundError in the case of deletion).

Since Database objects work on a snapshot of the database's state, the
situation above can only happen with a WritableDatabase object, or if
you call Database::reopen() on a Database object.

We recommend you avoid designs where this behaviour is an issue, but
if you need a way to make a non-lazy version of a Document object, you
can do this like so:

doc = Xapian::Document::unserialise(doc.serialise()); ";

%feature("docstring")  Xapian::Document::Document "

Copying is allowed.

Xapian::Document::Document(const Document &other)

The internals are reference counted, so copying is cheap. ";

%feature("docstring")  Xapian::Document::Document "

Make a new empty Document.

Xapian::Document::Document() ";

%feature("docstring")  Xapian::Document::~Document "

Destructor.

Xapian::Document::~Document() ";

%feature("docstring")  Xapian::Document::get_value "

Get value by number.

std::string Xapian::Document::get_value(Xapian::valueno slot) const

Returns an empty string if no value with the given number is present
in the document.

Parameters:
-----------

slot:  The number of the value. ";

%feature("docstring")  Xapian::Document::add_value "

Add a new value.

void Xapian::Document::add_value(Xapian::valueno slot, const
std::string &value)

The new value will replace any existing value with the same number (or
if the new value is empty, it will remove any existing value with the
same number). ";

%feature("docstring")  Xapian::Document::remove_value "

Remove any value with the given number.

void Xapian::Document::remove_value(Xapian::valueno slot) ";

%feature("docstring")  Xapian::Document::clear_values "

Remove all values associated with the document.

void Xapian::Document::clear_values() ";

%feature("docstring")  Xapian::Document::get_data "

Get data stored in the document.

std::string Xapian::Document::get_data() const

This is a potentially expensive operation, and shouldn't normally be
used in a match decider functor. Put data for use by match deciders in
a value instead. ";

%feature("docstring")  Xapian::Document::set_data "

Set data stored in the document.

void Xapian::Document::set_data(const std::string &data) ";

%feature("docstring")  Xapian::Document::add_posting "

Add an occurrence of a term at a particular position.

void Xapian::Document::add_posting(const std::string &tname,
Xapian::termpos tpos, Xapian::termcount wdfinc=1)

Multiple occurrences of the term at the same position are represented
only once in the positional information, but do increase the wdf.

If the term is not already in the document, it will be added to it.

Parameters:
-----------

tname:  The name of the term.

tpos:  The position of the term.

wdfinc:  The increment that will be applied to the wdf for this term.
";

%feature("docstring")  Xapian::Document::add_term "

Add a term to the document, without positional information.

void Xapian::Document::add_term(const std::string &tname,
Xapian::termcount wdfinc=1)

Any existing positional information for the term will be left
unmodified.

Parameters:
-----------

tname:  The name of the term.

wdfinc:  The increment that will be applied to the wdf for this term
(default: 1). ";

%feature("docstring")  Xapian::Document::add_boolean_term "

Add a boolean filter term to the document.

void Xapian::Document::add_boolean_term(const std::string &term)

This method adds term to the document with wdf of 0 - this is
generally what you want for a term used for boolean filtering as the
wdf of such terms is ignored, and it doesn't make sense for them to
contribute to the document's length.

If the specified term already indexes this document, this method has
no effect.

It is exactly the same as add_term(term, 0).

This method was added in Xapian 1.0.18.

Parameters:
-----------

term:  The term to add. ";

%feature("docstring")  Xapian::Document::remove_posting "

Remove a posting of a term from the document.

void Xapian::Document::remove_posting(const std::string &tname,
Xapian::termpos tpos, Xapian::termcount wdfdec=1)

Note that the term will still index the document even if all
occurrences are removed. To remove a term from a document completely,
use remove_term().

Parameters:
-----------

tname:  The name of the term.

tpos:  The position of the term.

wdfdec:  The decrement that will be applied to the wdf when removing
this posting. The wdf will not go below the value of 0.

Parameters:
-----------

Xapian::InvalidArgumentError:  will be thrown if the term is not at
the position specified in the position list for this term in this
document.

Xapian::InvalidArgumentError:  will be thrown if the term is not in
the document ";

%feature("docstring")  Xapian::Document::remove_term "

Remove a term and all postings associated with it.

void Xapian::Document::remove_term(const std::string &tname)

Parameters:
-----------

tname:  The name of the term.

Parameters:
-----------

Xapian::InvalidArgumentError:  will be thrown if the term is not in
the document ";

%feature("docstring")  Xapian::Document::clear_terms "

Remove all terms (and postings) from the document.

void Xapian::Document::clear_terms() ";

%feature("docstring")  Xapian::Document::termlist_count "

The length of the termlist - i.e.

Xapian::termcount Xapian::Document::termlist_count() const

the number of different terms which index this document. ";

%feature("docstring")  Xapian::Document::termlist_begin "

Iterator for the terms in this document.

TermIterator Xapian::Document::termlist_begin() const ";

%feature("docstring")  Xapian::Document::termlist_end "

Equivalent end iterator for termlist_begin().

TermIterator Xapian::Document::termlist_end() const ";

%feature("docstring")  Xapian::Document::values_count "

Count the values in this document.

Xapian::termcount Xapian::Document::values_count() const ";

%feature("docstring")  Xapian::Document::values_begin "

Iterator for the values in this document.

ValueIterator Xapian::Document::values_begin() const ";

%feature("docstring")  Xapian::Document::values_end "

Equivalent end iterator for values_begin().

ValueIteratorEnd_ Xapian::Document::values_end() const ";

%feature("docstring")  Xapian::Document::get_docid "

Get the document id which is associated with this document (if any).

docid Xapian::Document::get_docid() const

NB If multiple databases are being searched together, then this will
be the document id in the individual database, not the merged
database!

If this document came from a database, return the document id in that
database. Otherwise, return 0 (in Xapian 1.0.22/1.2.4 or later; prior
to this the returned value was uninitialised). ";

%feature("docstring")  Xapian::Document::serialise "

Serialise document into a string.

std::string Xapian::Document::serialise() const

The document representation may change between Xapian releases: even
between minor versions. However, it is guaranteed not to change if the
remote database protocol has not changed between releases. ";

%feature("docstring")  Xapian::Document::get_description "

Return a string describing this object.

std::string Xapian::Document::get_description() const ";


// File: classstd_1_1domain__error.xml
%feature("docstring") std::domain_error "

STL class. ";


// File: classXapian_1_1Enquire.xml
%feature("docstring") Xapian::Enquire "

This class provides an interface to the information retrieval system
for the purpose of searching.

Databases are usually opened lazily, so exceptions may not be thrown
where you would expect them to be. You should catch Xapian::Error
exceptions when calling any method in Xapian::Enquire.

Parameters:
-----------

Xapian::InvalidArgumentError:  will be thrown if an invalid argument
is supplied, for example, an unknown database type. ";

%feature("docstring")  Xapian::Enquire::Enquire "

Copying is allowed (and is cheap).

Xapian::Enquire::Enquire(const Enquire &other) ";

%feature("docstring")  Xapian::Enquire::Enquire "

Create a Xapian::Enquire object.

Xapian::Enquire::Enquire(const Database &database, ErrorHandler
*errorhandler_=0)

This specification cannot be changed once the Xapian::Enquire is
opened: you must create a new Xapian::Enquire object to access a
different database, or set of databases.

The database supplied must have been initialised (ie, must not be the
result of calling the Database::Database() constructor). If you need
to handle a situation where you have no index gracefully, a database
created with InMemory::open() can be passed here, which represents a
completely empty database.

Parameters:
-----------

database:  Specification of the database or databases to use.

errorhandler_:  A pointer to the error handler to use. Ownership of
the object pointed to is not assumed by the Xapian::Enquire object -
the user should delete the Xapian::ErrorHandler object after the
Xapian::Enquire object is deleted. To use no error handler, this
parameter should be 0.

Parameters:
-----------

Xapian::InvalidArgumentError:  will be thrown if an initialised
Database object is supplied. ";

%feature("docstring")  Xapian::Enquire::~Enquire "

Close the Xapian::Enquire object.

Xapian::Enquire::~Enquire() ";

%feature("docstring")  Xapian::Enquire::set_query "

Set the query to run.

void Xapian::Enquire::set_query(const Xapian::Query &query,
Xapian::termcount qlen=0)

Parameters:
-----------

query:  the new query to run.

qlen:  the query length to use in weight calculations - by default the
sum of the wqf of all terms is used. ";

%feature("docstring")  Xapian::Enquire::get_query "

Get the query which has been set.

const Xapian::Query& Xapian::Enquire::get_query() const

This is only valid after set_query() has been called.

Parameters:
-----------

Xapian::InvalidArgumentError:  will be thrown if query has not yet
been set. ";

%feature("docstring")  Xapian::Enquire::add_matchspy "

Add a matchspy.

void Xapian::Enquire::add_matchspy(MatchSpy *spy)

This matchspy will be called with some of the documents which match
the query, during the match process. Exactly which of the matching
documents are passed to it depends on exactly when certain
optimisations occur during the match process, but it can be controlled
to some extent by setting the checkatleast parameter to  get_mset().

In particular, if there are enough matching documents, at least the
number specified by checkatleast will be passed to the matchspy. This
means that you can force the matchspy to be shown all matching
documents by setting checkatleast to the number of documents in the
database.

Parameters:
-----------

spy:  The MatchSpy subclass to add. The caller must ensure that this
remains valid while the Enquire object remains active, or until
clear_matchspies() is called. ";

%feature("docstring")  Xapian::Enquire::clear_matchspies "

Remove all the matchspies.

void Xapian::Enquire::clear_matchspies() ";

%feature("docstring")  Xapian::Enquire::set_weighting_scheme "

Set the weighting scheme to use for queries.

void Xapian::Enquire::set_weighting_scheme(const Weight &weight_)

Parameters:
-----------

weight_:  the new weighting scheme. If no weighting scheme is
specified, the default is BM25 with the default parameters. ";

%feature("docstring")  Xapian::Enquire::set_collapse_key "

Set the collapse key to use for queries.

void Xapian::Enquire::set_collapse_key(Xapian::valueno collapse_key,
Xapian::doccount collapse_max=1)

Parameters:
-----------

collapse_key:  value number to collapse on - at most one MSet entry
with each particular value will be returned (default is
Xapian::BAD_VALUENO which means no collapsing).

collapse_max:  Max number of items with the same key to leave after
collapsing (default 1).

The MSet returned by get_mset() will have only the \"best\" (at most)
collapse_max entries with each particular value of collapse_key
(\"best\" being highest ranked - i.e. highest weight or highest
sorting key).

An example use might be to create a value for each document containing
an MD5 hash of the document contents. Then duplicate documents from
different sources can be eliminated at search time by collapsing with
collapse_max = 1 (it's better to eliminate duplicates at index time,
but this may not be always be possible - for example the search may be
over more than one Xapian database).

Another use is to group matches in a particular category (e.g. you
might collapse a mailing list search on the Subject: so that there's
only one result per discussion thread). In this case you can use
get_collapse_count() to give the user some idea how many other results
there are. And if you index the Subject: as a boolean term as well as
putting it in a value, you can offer a link to a non-collapsed search
restricted to that thread using a boolean filter. ";

%feature("docstring")  Xapian::Enquire::set_docid_order "

Set the direction in which documents are ordered by document id in the
returned MSet.

void Xapian::Enquire::set_docid_order(docid_order order)

This order only has an effect on documents which would otherwise have
equal rank. For a weighted probabilistic match with no sort value,
this means documents with equal weight. For a boolean match, with no
sort value, this means all documents. And if a sort value is used,
this means documents with equal sort value (and also equal weight if
ordering on relevance after the sort).

Parameters:
-----------

order:  This can be: Xapian::Enquire::ASCENDING docids sort in
ascending order (default)

Xapian::Enquire::DESCENDING docids sort in descending order

Xapian::Enquire::DONT_CARE docids sort in whatever order is most
efficient for the backend

Note: If you add documents in strict date order, then a boolean search
- i.e. set_weighting_scheme(Xapian::BoolWeight()) - with
set_docid_order(Xapian::Enquire::DESCENDING) is a very efficient way
to perform \"sort by date, newest first\". ";

%feature("docstring")  Xapian::Enquire::set_cutoff "

Set the percentage and/or weight cutoffs.

void Xapian::Enquire::set_cutoff(Xapian::percent percent_cutoff,
Xapian::weight weight_cutoff=0)

Parameters:
-----------

percent_cutoff:  Minimum percentage score for returned documents. If a
document has a lower percentage score than this, it will not appear in
the MSet. If your intention is to return only matches which contain
all the terms in the query, then it's more efficient to use
Xapian::Query::OP_AND instead of Xapian::Query::OP_OR in the query
than to use set_cutoff(100). (default 0 => no percentage cut-off).

weight_cutoff:  Minimum weight for a document to be returned. If a
document has a lower score that this, it will not appear in the MSet.
It is usually only possible to choose an appropriate weight for cutoff
based on the results of a previous run of the same query; this is thus
mainly useful for alerting operations. The other potential use is with
a user specified weighting scheme. (default 0 => no weight cut-off).
";

%feature("docstring")  Xapian::Enquire::set_sort_by_relevance "

Set the sorting to be by relevance only.

void Xapian::Enquire::set_sort_by_relevance()

This is the default. ";

%feature("docstring")  Xapian::Enquire::set_sort_by_value "

Set the sorting to be by value only.

void Xapian::Enquire::set_sort_by_value(Xapian::valueno sort_key, bool
reverse)

Note that sorting by values uses a string comparison, so to use this
to sort by a numeric value you'll need to store the numeric values in
a manner which sorts appropriately. For example, you could use
Xapian::sortable_serialise() (which works for floating point numbers
as well as integers), or store numbers padded with leading zeros or
spaces, or with the number of digits prepended.

Parameters:
-----------

sort_key:  value number to sort on.

reverse:  If true, reverses the sort order. ";

%feature("docstring")  Xapian::Enquire::set_sort_by_value "void
Xapian::Enquire::set_sort_by_value(Xapian::valueno sort_key) ";

%feature("docstring")  Xapian::Enquire::set_sort_by_key "

Set the sorting to be by key generated from values only.

void Xapian::Enquire::set_sort_by_key(Xapian::KeyMaker *sorter, bool
reverse)

Parameters:
-----------

sorter:  The functor to use for generating keys.

reverse:  If true, reverses the sort order. ";

%feature("docstring")  Xapian::Enquire::set_sort_by_key "void
Xapian::Enquire::set_sort_by_key(Xapian::KeyMaker *sorter) ";

%feature("docstring")
Xapian::Enquire::set_sort_by_value_then_relevance "

Set the sorting to be by value, then by relevance for documents with
the same value.

void Xapian::Enquire::set_sort_by_value_then_relevance(Xapian::valueno
sort_key, bool reverse)

Note that sorting by values uses a string comparison, so to use this
to sort by a numeric value you'll need to store the numeric values in
a manner which sorts appropriately. For example, you could use
Xapian::sortable_serialise() (which works for floating point numbers
as well as integers), or store numbers padded with leading zeros or
spaces, or with the number of digits prepended.

Parameters:
-----------

sort_key:  value number to sort on.

reverse:  If true, reverses the sort order. ";

%feature("docstring")
Xapian::Enquire::set_sort_by_value_then_relevance "void
Xapian::Enquire::set_sort_by_value_then_relevance(Xapian::valueno
sort_key) ";

%feature("docstring")  Xapian::Enquire::set_sort_by_key_then_relevance
"

Set the sorting to be by keys generated from values, then by relevance
for documents with identical keys.

void Xapian::Enquire::set_sort_by_key_then_relevance(Xapian::KeyMaker
*sorter, bool reverse)

Parameters:
-----------

sorter:  The functor to use for generating keys.

reverse:  If true, reverses the sort order. ";

%feature("docstring")  Xapian::Enquire::set_sort_by_key_then_relevance
"void
Xapian::Enquire::set_sort_by_key_then_relevance(Xapian::KeyMaker
*sorter) ";

%feature("docstring")
Xapian::Enquire::set_sort_by_relevance_then_value "

Set the sorting to be by relevance then value.

void Xapian::Enquire::set_sort_by_relevance_then_value(Xapian::valueno
sort_key, bool reverse)

Note that sorting by values uses a string comparison, so to use this
to sort by a numeric value you'll need to store the numeric values in
a manner which sorts appropriately. For example, you could use
Xapian::sortable_serialise() (which works for floating point numbers
as well as integers), or store numbers padded with leading zeros or
spaces, or with the number of digits prepended.

Note that with the default BM25 weighting scheme parameters, non-
identical documents will rarely have the same weight, so this setting
will give very similar results to set_sort_by_relevance(). It becomes
more useful with particular BM25 parameter settings (e.g.
BM25Weight(1,0,1,0,0)) or custom weighting schemes.

Parameters:
-----------

sort_key:  value number to sort on.

reverse:  If true, reverses the sort order. ";

%feature("docstring")
Xapian::Enquire::set_sort_by_relevance_then_value "void
Xapian::Enquire::set_sort_by_relevance_then_value(Xapian::valueno
sort_key) ";

%feature("docstring")  Xapian::Enquire::set_sort_by_relevance_then_key
"

Set the sorting to be by relevance, then by keys generated from
values.

void Xapian::Enquire::set_sort_by_relevance_then_key(Xapian::KeyMaker
*sorter, bool reverse)

Note that with the default BM25 weighting scheme parameters, non-
identical documents will rarely have the same weight, so this setting
will give very similar results to set_sort_by_relevance(). It becomes
more useful with particular BM25 parameter settings (e.g.
BM25Weight(1,0,1,0,0)) or custom weighting schemes.

Parameters:
-----------

sorter:  The functor to use for generating keys.

reverse:  If true, reverses the sort order. ";

%feature("docstring")  Xapian::Enquire::set_sort_by_relevance_then_key
"void
Xapian::Enquire::set_sort_by_relevance_then_key(Xapian::KeyMaker
*sorter) ";

%feature("docstring")  Xapian::Enquire::get_eset "

Get the expand set for the given rset.

ESet Xapian::Enquire::get_eset(Xapian::termcount maxitems, const RSet
&omrset, int flags=0, double k=1.0, const Xapian::ExpandDecider
*edecider=0) const

Parameters:
-----------

maxitems:  the maximum number of items to return.

omrset:  the relevance set to use when performing the expand
operation.

flags:  zero or more of these values |-ed together:
Xapian::Enquire::INCLUDE_QUERY_TERMS query terms may be returned from
expand

Xapian::Enquire::USE_EXACT_TERMFREQ for multi dbs, calculate the exact
termfreq; otherwise an approximation is used which can greatly improve
efficiency, but still returns good results.

k:  the parameter k in the query expansion algorithm (default is 1.0)

edecider:  a decision functor to use to decide whether a given term
should be put in the ESet

min_wt:  the minimum weight for included terms

An ESet object containing the results of the expand.

Parameters:
-----------

Xapian::InvalidArgumentError:  See class documentation. ";

%feature("docstring")  Xapian::Enquire::get_eset "

Get the expand set for the given rset.

ESet Xapian::Enquire::get_eset(Xapian::termcount maxitems, const RSet
&omrset, const Xapian::ExpandDecider *edecider) const

Parameters:
-----------

maxitems:  the maximum number of items to return.

omrset:  the relevance set to use when performing the expand
operation.

edecider:  a decision functor to use to decide whether a given term
should be put in the ESet

An ESet object containing the results of the expand.

Parameters:
-----------

Xapian::InvalidArgumentError:  See class documentation. ";

%feature("docstring")  Xapian::Enquire::get_eset "

Get the expand set for the given rset.

ESet Xapian::Enquire::get_eset(Xapian::termcount maxitems, const RSet
&omrset, int flags, double k, const Xapian::ExpandDecider *edecider,
Xapian::weight min_wt) const

Parameters:
-----------

maxitems:  the maximum number of items to return.

omrset:  the relevance set to use when performing the expand
operation.

flags:  zero or more of these values |-ed together:
Xapian::Enquire::INCLUDE_QUERY_TERMS query terms may be returned from
expand

Xapian::Enquire::USE_EXACT_TERMFREQ for multi dbs, calculate the exact
termfreq; otherwise an approximation is used which can greatly improve
efficiency, but still returns good results.

k:  the parameter k in the query expansion algorithm (default is 1.0)

edecider:  a decision functor to use to decide whether a given term
should be put in the ESet

min_wt:  the minimum weight for included terms

An ESet object containing the results of the expand.

Parameters:
-----------

Xapian::InvalidArgumentError:  See class documentation. ";

%feature("docstring")  Xapian::Enquire::get_matching_terms_begin "

Get terms which match a given document, by document id.

TermIterator Xapian::Enquire::get_matching_terms_begin(Xapian::docid
did) const

This method returns the terms in the current query which match the
given document.

It is possible for the document to have been removed from the database
between the time it is returned in an MSet, and the time that this
call is made. If possible, you should specify an MSetIterator instead
of a Xapian::docid, since this will enable database backends with
suitable support to prevent this occurring.

Note that a query does not need to have been run in order to make this
call.

Parameters:
-----------

did:  The document id for which to retrieve the matching terms.

An iterator returning the terms which match the document. The terms
will be returned (as far as this makes any sense) in the same order as
the terms in the query. Terms will not occur more than once, even if
they do in the query.

Parameters:
-----------

Xapian::InvalidArgumentError:  See class documentation.

Xapian::DocNotFoundError:  The document specified could not be found
in the database. ";

%feature("docstring")  Xapian::Enquire::get_matching_terms_end "

End iterator corresponding to get_matching_terms_begin().

TermIterator Xapian::Enquire::get_matching_terms_end(Xapian::docid)
const ";

%feature("docstring")  Xapian::Enquire::get_matching_terms_begin "

Get terms which match a given document, by match set item.

TermIterator Xapian::Enquire::get_matching_terms_begin(const
MSetIterator &it) const

This method returns the terms in the current query which match the
given document.

If the underlying database has suitable support, using this call
(rather than passing a Xapian::docid) will enable the system to ensure
that the correct data is returned, and that the document has not been
deleted or changed since the query was performed.

Parameters:
-----------

it:  The iterator for which to retrieve the matching terms.

An iterator returning the terms which match the document. The terms
will be returned (as far as this makes any sense) in the same order as
the terms in the query. Terms will not occur more than once, even if
they do in the query.

Parameters:
-----------

Xapian::InvalidArgumentError:  See class documentation.

Xapian::DocNotFoundError:  The document specified could not be found
in the database. ";

%feature("docstring")  Xapian::Enquire::get_matching_terms_end "

End iterator corresponding to get_matching_terms_begin().

TermIterator Xapian::Enquire::get_matching_terms_end(const
MSetIterator &) const ";

%feature("docstring")  Xapian::Enquire::get_description "

Return a string describing this object.

std::string Xapian::Enquire::get_description() const ";


// File: classXapian_1_1Error.xml
%feature("docstring") Xapian::Error "

All exceptions thrown by Xapian are subclasses of Xapian::Error.

This class can not be instantiated directly - instead a subclass
should be used. ";

%feature("docstring")  Xapian::Error::get_type "

The type of this error (e.g. \"DocNotFoundError\".).

const char* Xapian::Error::get_type() const ";

%feature("docstring")  Xapian::Error::get_msg "

Message giving details of the error, intended for human consumption.

const std::string& Xapian::Error::get_msg() const ";

%feature("docstring")  Xapian::Error::get_context "

Optional context information.

const std::string& Xapian::Error::get_context() const

This context is intended for use by Xapian::ErrorHandler (for example
so it can know which remote server is unreliable and report the
problem and remove that server from those being searched). But it's
typically a plain-text string, and so also fit for human consumption.
";

%feature("docstring")  Xapian::Error::get_error_string "

Returns any system error string associated with this exception.

const char* Xapian::Error::get_error_string() const

The system error string may come from errno, h_errno (on UNIX), or
GetLastError() (on MS Windows). If there is no associated system error
string, NULL is returned. ";

%feature("docstring")  Xapian::Error::get_description "

Return a string describing this object.

std::string Xapian::Error::get_description() const ";


// File: classXapian_1_1ErrorHandler.xml
%feature("docstring") Xapian::ErrorHandler "

Decide if a Xapian::Error exception should be ignored.

You can create your own subclass of this class and pass in an instance
of it when you construct a Xapian::Enquire object. Xapian::Error
exceptions which happen during the match process are passed to this
object and it can decide whether they should propagate or whether
Enquire should attempt to continue.

The motivation is to allow searching over remote databases to handle a
remote server which has died (both to allow results to be returned,
and also so that such errors can be logged and dead servers
temporarily removed from use). ";

%feature("docstring")  Xapian::ErrorHandler::ErrorHandler "

Default constructor.

Xapian::ErrorHandler::ErrorHandler() ";

%feature("docstring")  Xapian::ErrorHandler::~ErrorHandler "

We require a virtual destructor because we have virtual methods.

virtual Xapian::ErrorHandler::~ErrorHandler() ";


// File: classXapian_1_1ESet.xml
%feature("docstring") Xapian::ESet "

Class representing an ordered set of expand terms (an ESet).

This set represents the results of an expand operation, which is
performed by Xapian::Enquire::get_eset(). ";

%feature("docstring")  Xapian::ESet::ESet "

Construct an empty ESet.

Xapian::ESet::ESet() ";

%feature("docstring")  Xapian::ESet::~ESet "

Destructor.

Xapian::ESet::~ESet() ";

%feature("docstring")  Xapian::ESet::ESet "

Copying is allowed (and is cheap).

Xapian::ESet::ESet(const ESet &other) ";

%feature("docstring")  Xapian::ESet::get_ebound "

A lower bound on the number of terms which are in the full set of
results of the expand.

Xapian::termcount Xapian::ESet::get_ebound() const

This will be greater than or equal to size() ";

%feature("docstring")  Xapian::ESet::size "

The number of terms in this E-Set.

Xapian::termcount Xapian::ESet::size() const ";

%feature("docstring")  Xapian::ESet::max_size "

Required to allow use as an STL container.

Xapian::termcount Xapian::ESet::max_size() const ";

%feature("docstring")  Xapian::ESet::empty "

Test if this E-Set is empty.

bool Xapian::ESet::empty() const ";

%feature("docstring")  Xapian::ESet::swap "

Swap the E-Set we point to with another.

void Xapian::ESet::swap(ESet &other) ";

%feature("docstring")  Xapian::ESet::begin "

Iterator for the terms in this E-Set.

ESetIterator Xapian::ESet::begin() const ";

%feature("docstring")  Xapian::ESet::end "

End iterator corresponding to begin().

ESetIterator Xapian::ESet::end() const ";

%feature("docstring")  Xapian::ESet::back "

Iterator pointing to the last element of this E-Set.

ESetIterator Xapian::ESet::back() const ";

%feature("docstring")  Xapian::ESet::get_description "

Return a string describing this object.

std::string Xapian::ESet::get_description() const ";


// File: classXapian_1_1ESetIterator.xml
%feature("docstring") Xapian::ESetIterator "

Iterate through terms in the ESet. ";

%feature("docstring")  Xapian::ESetIterator::ESetIterator "

Create an uninitialised iterator; this cannot be used, but is
convenient syntactically.

Xapian::ESetIterator::ESetIterator() ";

%feature("docstring")  Xapian::ESetIterator::ESetIterator "

Copying is allowed (and is cheap).

Xapian::ESetIterator::ESetIterator(const ESetIterator &other) ";

%feature("docstring")  Xapian::ESetIterator::get_weight "

Get the weight of the term at the current position.

Xapian::weight Xapian::ESetIterator::get_weight() const ";

%feature("docstring")  Xapian::ESetIterator::get_description "

Return a string describing this object.

std::string Xapian::ESetIterator::get_description() const ";


// File: classstd_1_1exception.xml
%feature("docstring") std::exception "

STL class. ";


// File: classXapian_1_1ExpandDecider.xml
%feature("docstring") Xapian::ExpandDecider "

Virtual base class for expand decider functor. ";

%feature("docstring")  Xapian::ExpandDecider::~ExpandDecider "

Virtual destructor, because we have virtual methods.

virtual Xapian::ExpandDecider::~ExpandDecider() ";


// File: classXapian_1_1ExpandDeciderAnd.xml
%feature("docstring") Xapian::ExpandDeciderAnd "

ExpandDecider subclass which rejects terms using two ExpandDeciders.

Terms are only accepted if they are accepted by both of the specified
ExpandDecider objects. ";

%feature("docstring")  Xapian::ExpandDeciderAnd::ExpandDeciderAnd "

Terms will be checked with first, and if accepted, then checked with
second.

Xapian::ExpandDeciderAnd::ExpandDeciderAnd(const ExpandDecider
&first_, const ExpandDecider &second_) ";

%feature("docstring")  Xapian::ExpandDeciderAnd::ExpandDeciderAnd "

Compatibility method.

Xapian::ExpandDeciderAnd::ExpandDeciderAnd(const ExpandDecider
*first_, const ExpandDecider *second_) ";


// File: classXapian_1_1ExpandDeciderFilterTerms.xml
%feature("docstring") Xapian::ExpandDeciderFilterTerms "

ExpandDecider subclass which rejects terms in a specified list.

ExpandDeciderFilterTerms provides an easy way to filter out terms from
a fixed list when generating an ESet. ";

%feature("docstring")
Xapian::ExpandDeciderFilterTerms::ExpandDeciderFilterTerms "

The two iterators specify a list of terms to be rejected.

Xapian::ExpandDeciderFilterTerms::ExpandDeciderFilterTerms(Iterator
reject_begin, Iterator reject_end)

reject_begin and reject_end can be any input_iterator type which
returns std::string or char * (e.g. TermIterator or char **). ";


// File: classstd_1_1ios__base_1_1failure.xml
%feature("docstring") std::ios_base::failure "

STL class. ";


// File: classXapian_1_1FeatureUnavailableError.xml
%feature("docstring") Xapian::FeatureUnavailableError "

Indicates an attempt to use a feature which is unavailable.

Typically a feature is unavailable because it wasn't compiled in, or
because it requires other software or facilities which aren't
available. ";

%feature("docstring")
Xapian::FeatureUnavailableError::FeatureUnavailableError "

General purpose constructor which allows setting errno.

Xapian::FeatureUnavailableError::FeatureUnavailableError(const
std::string &msg_, const std::string &context_=std::string(), int
errno_=0) ";

%feature("docstring")
Xapian::FeatureUnavailableError::FeatureUnavailableError "

Construct from message and errno value.

Xapian::FeatureUnavailableError::FeatureUnavailableError(const
std::string &msg_, int errno_) ";


// File: classXapian_1_1FixedWeightPostingSource.xml
%feature("docstring") Xapian::FixedWeightPostingSource "

A posting source which returns a fixed weight for all documents.

This returns entries for all documents in the given database, with a
fixed weight (specified by a parameter to the constructor). ";

%feature("docstring")
Xapian::FixedWeightPostingSource::FixedWeightPostingSource "

Construct a FixedWeightPostingSource.

Xapian::FixedWeightPostingSource::FixedWeightPostingSource(Xapian::weight
wt)

Parameters:
-----------

wt:  The fixed weight to return. ";

%feature("docstring")
Xapian::FixedWeightPostingSource::get_termfreq_min "

A lower bound on the number of documents this object can return.

Xapian::doccount Xapian::FixedWeightPostingSource::get_termfreq_min()
const

Xapian will always call init() on a PostingSource before calling this
for the first time. ";

%feature("docstring")
Xapian::FixedWeightPostingSource::get_termfreq_est "

An estimate of the number of documents this object can return.

Xapian::doccount Xapian::FixedWeightPostingSource::get_termfreq_est()
const

It must always be true that:

get_termfreq_min() <= get_termfreq_est() <= get_termfreq_max()

Xapian will always call init() on a PostingSource before calling this
for the first time. ";

%feature("docstring")
Xapian::FixedWeightPostingSource::get_termfreq_max "

An upper bound on the number of documents this object can return.

Xapian::doccount Xapian::FixedWeightPostingSource::get_termfreq_max()
const

Xapian will always call init() on a PostingSource before calling this
for the first time. ";

%feature("docstring")  Xapian::FixedWeightPostingSource::get_weight "

Return the weight contribution for the current document.

Xapian::weight Xapian::FixedWeightPostingSource::get_weight() const

This default implementation always returns 0, for convenience when
implementing \"weight-less\" PostingSource subclasses.

This method may assume that it will only be called when there is a
\"current document\". In detail: Xapian will always call init() on a
PostingSource before calling this for the first time. It will also
only call this if the PostingSource reports that it is pointing to a
valid document (ie, it will not call it before calling at least one of
next(), skip_to() or check(), and will ensure that the PostingSource
is not at the end by calling at_end()). ";

%feature("docstring")  Xapian::FixedWeightPostingSource::next "

Advance the current position to the next matching document.

void Xapian::FixedWeightPostingSource::next(Xapian::weight min_wt)

The PostingSource starts before the first entry in the list, so next()
must be called before any methods which need the context of the
current position.

Xapian will always call init() on a PostingSource before calling this
for the first time.

Parameters:
-----------

min_wt:  The minimum weight contribution that is needed (this is just
a hint which subclasses may ignore). ";

%feature("docstring")  Xapian::FixedWeightPostingSource::skip_to "

Advance to the specified docid.

void Xapian::FixedWeightPostingSource::skip_to(Xapian::docid
min_docid, Xapian::weight min_wt)

If the specified docid isn't in the list, position ourselves on the
first document after it (or at_end() if no greater docids are
present).

If the current position is already the specified docid, this method
will leave the position unmodified.

If the specified docid is earlier than the current position, the
behaviour is unspecified. A sensible behaviour would be to leave the
current position unmodified, but it is also reasonable to move to the
specified docid.

The default implementation calls next() repeatedly, which works but
skip_to() can often be implemented much more efficiently.

Xapian will always call init() on a PostingSource before calling this
for the first time.

Note: in the case of a multi-database search, the docid specified is
the docid in the single subdatabase relevant to this posting source.
See the  init() method for details.

Parameters:
-----------

min_wt:  The minimum weight contribution that is needed (this is just
a hint which subclasses may ignore). ";

%feature("docstring")  Xapian::FixedWeightPostingSource::check "

Check if the specified docid occurs.

bool Xapian::FixedWeightPostingSource::check(Xapian::docid min_docid,
Xapian::weight min_wt)

The caller is required to ensure that the specified document id did
actually exists in the database. If it does, it must move to that
document id, and return true. If it does not, it may either:

return true, having moved to a definite position (including
\"at_end\"), which must be the same position as skip_to() would have
moved to.

or

return false, having moved to an \"indeterminate\" position, such that
a subsequent call to next() or skip_to() will move to the next
matching position after did.

Generally, this method should act like skip_to() and return true if
that can be done at little extra cost.

Otherwise it should simply check if a particular docid is present,
returning true if it is, and false if it isn't.

The default implementation calls skip_to() and always returns true.

Xapian will always call init() on a PostingSource before calling this
for the first time.

Note: in the case of a multi-database search, the docid specified is
the docid in the single subdatabase relevant to this posting source.
See the  init() method for details. ";

%feature("docstring")  Xapian::FixedWeightPostingSource::at_end "

Return true if the current position is past the last entry in this
list.

bool Xapian::FixedWeightPostingSource::at_end() const

At least one of  next(),  skip_to() or  check() will be called before
this method is first called. ";

%feature("docstring")  Xapian::FixedWeightPostingSource::get_docid "

Return the current docid.

Xapian::docid Xapian::FixedWeightPostingSource::get_docid() const

This method may assume that it will only be called when there is a
\"current document\". See  get_weight() for details.

Note: in the case of a multi-database search, the returned docid
should be in the single subdatabase relevant to this posting source.
See the  init() method for details. ";

%feature("docstring")  Xapian::FixedWeightPostingSource::clone "

Clone the posting source.

FixedWeightPostingSource* Xapian::FixedWeightPostingSource::clone()
const

The clone should inherit the configuration of the parent, but need not
inherit the state. ie, the clone does not need to be in the same
iteration position as the original: the matcher will always call
init() on the clone before attempting to move the iterator, or read
the information about the current position of the iterator.

This may return NULL to indicate that cloning is not supported. In
this case, the PostingSource may only be used with a single-database
search.

The default implementation returns NULL.

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".
";

%feature("docstring")  Xapian::FixedWeightPostingSource::name "

Name of the posting source class.

std::string Xapian::FixedWeightPostingSource::name() const

This is used when serialising and unserialising posting sources; for
example, for performing remote searches.

If the subclass is in a C++ namespace, the namespace should be
included in the name, using \"::\" as a separator. For example, for a
PostingSource subclass called \"FooPostingSource\" in the \"Xapian\"
namespace the result of this call should be
\"Xapian::FooPostingSource\".

This should only be implemented if serialise() and unserialise() are
also implemented. The default implementation returns an empty string.

If this returns an empty string, Xapian will assume that serialise()
and unserialise() are not implemented. ";

%feature("docstring")  Xapian::FixedWeightPostingSource::serialise "

Serialise object parameters into a string.

std::string Xapian::FixedWeightPostingSource::serialise() const

The serialised parameters should represent the configuration of the
posting source, but need not (indeed, should not) represent the
current iteration state.

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.
";

%feature("docstring")  Xapian::FixedWeightPostingSource::unserialise "

Create object given string serialisation returned by serialise().

FixedWeightPostingSource*
Xapian::FixedWeightPostingSource::unserialise(const std::string &s)
const

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.

Parameters:
-----------

s:  A serialised instance of this PostingSource subclass. ";

%feature("docstring")  Xapian::FixedWeightPostingSource::init "

Set this PostingSource to the start of the list of postings.

void Xapian::FixedWeightPostingSource::init(const Database &db_)

This is called automatically by the matcher prior to each query being
processed.

If a PostingSource is used for multiple searches,  init() will
therefore be called multiple times, and must handle this by using the
database passed in the most recent call.

Parameters:
-----------

db:  The database which the PostingSource should iterate through.

Note: the database supplied to this method must not be modified: in
particular, the reopen() method should not be called on it.

Note: in the case of a multi-database search, a separate PostingSource
will be used for each database (the separate PostingSources will be
obtained using  clone()), and each PostingSource will be passed one of
the sub-databases as the db parameter here. The db parameter will
therefore always refer to a single database. All docids passed to, or
returned from, the PostingSource refer to docids in that single
database, rather than in the multi- database. ";

%feature("docstring")
Xapian::FixedWeightPostingSource::get_description "

Return a string describing this object.

std::string Xapian::FixedWeightPostingSource::get_description() const

This default implementation returns a generic answer. This default it
provided to avoid forcing those deriving their own PostingSource
subclass from having to implement this (they may not care what
get_description() gives for their subclass). ";


// File: classstd_1_1fstream.xml
%feature("docstring") std::fstream "

STL class. ";


// File: classstd_1_1ifstream.xml
%feature("docstring") std::ifstream "

STL class. ";


// File: structXapian_1_1ValueCountMatchSpy_1_1Internal.xml
%feature("docstring") Xapian::ValueCountMatchSpy::Internal "";

%feature("docstring")  Xapian::ValueCountMatchSpy::Internal::Internal
"Xapian::ValueCountMatchSpy::Internal::Internal() ";

%feature("docstring")  Xapian::ValueCountMatchSpy::Internal::Internal
"Xapian::ValueCountMatchSpy::Internal::Internal(Xapian::valueno
slot_) ";


// File: classXapian_1_1Query_1_1Internal.xml


// File: classXapian_1_1InternalError.xml
%feature("docstring") Xapian::InternalError "

InternalError indicates a runtime problem of some sort. ";

%feature("docstring")  Xapian::InternalError::InternalError "

General purpose constructor which allows setting errno.

Xapian::InternalError::InternalError(const std::string &msg_, const
std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")  Xapian::InternalError::InternalError "

Construct from message and errno value.

Xapian::InternalError::InternalError(const std::string &msg_, int
errno_) ";


// File: classstd_1_1invalid__argument.xml
%feature("docstring") std::invalid_argument "

STL class. ";


// File: classXapian_1_1InvalidArgumentError.xml
%feature("docstring") Xapian::InvalidArgumentError "

InvalidArgumentError indicates an invalid parameter value was passed
to the API. ";

%feature("docstring")
Xapian::InvalidArgumentError::InvalidArgumentError "

General purpose constructor which allows setting errno.

Xapian::InvalidArgumentError::InvalidArgumentError(const std::string
&msg_, const std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")
Xapian::InvalidArgumentError::InvalidArgumentError "

Construct from message and errno value.

Xapian::InvalidArgumentError::InvalidArgumentError(const std::string
&msg_, int errno_) ";


// File: classXapian_1_1InvalidOperationError.xml
%feature("docstring") Xapian::InvalidOperationError "

InvalidOperationError indicates the API was used in an invalid way. ";

%feature("docstring")
Xapian::InvalidOperationError::InvalidOperationError "

General purpose constructor which allows setting errno.

Xapian::InvalidOperationError::InvalidOperationError(const std::string
&msg_, const std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")
Xapian::InvalidOperationError::InvalidOperationError "

Construct from message and errno value.

Xapian::InvalidOperationError::InvalidOperationError(const std::string
&msg_, int errno_) ";


// File: classstd_1_1ios.xml
%feature("docstring") std::ios "

STL class. ";


// File: classstd_1_1ios__base.xml
%feature("docstring") std::ios_base "

STL class. ";


// File: classstd_1_1istream.xml
%feature("docstring") std::istream "

STL class. ";


// File: classstd_1_1istringstream.xml
%feature("docstring") std::istringstream "

STL class. ";


// File: classstd_1_1list_1_1iterator.xml
%feature("docstring") std::list::iterator "

STL iterator class. ";


// File: classstd_1_1map_1_1iterator.xml
%feature("docstring") std::map::iterator "

STL iterator class. ";


// File: classstd_1_1multimap_1_1iterator.xml
%feature("docstring") std::multimap::iterator "

STL iterator class. ";


// File: classstd_1_1set_1_1iterator.xml
%feature("docstring") std::set::iterator "

STL iterator class. ";


// File: classstd_1_1multiset_1_1iterator.xml
%feature("docstring") std::multiset::iterator "

STL iterator class. ";


// File: classstd_1_1vector_1_1iterator.xml
%feature("docstring") std::vector::iterator "

STL iterator class. ";


// File: classstd_1_1basic__string_1_1iterator.xml
%feature("docstring") std::basic_string::iterator "

STL iterator class. ";


// File: classstd_1_1string_1_1iterator.xml
%feature("docstring") std::string::iterator "

STL iterator class. ";


// File: classstd_1_1wstring_1_1iterator.xml
%feature("docstring") std::wstring::iterator "

STL iterator class. ";


// File: classstd_1_1deque_1_1iterator.xml
%feature("docstring") std::deque::iterator "

STL iterator class. ";


// File: classXapian_1_1KeyMaker.xml
%feature("docstring") Xapian::KeyMaker "

Virtual base class for key making functors. ";

%feature("docstring")  Xapian::KeyMaker::~KeyMaker "

Virtual destructor, because we have virtual methods.

virtual Xapian::KeyMaker::~KeyMaker() ";


// File: classstd_1_1length__error.xml
%feature("docstring") std::length_error "

STL class. ";


// File: classstd_1_1list.xml
%feature("docstring") std::list "

STL class. ";


// File: classstd_1_1logic__error.xml
%feature("docstring") std::logic_error "

STL class. ";


// File: classXapian_1_1LogicError.xml
%feature("docstring") Xapian::LogicError "

The base class for exceptions indicating errors in the program logic.

A subclass of LogicError will be thrown if Xapian detects a violation
of a class invariant or a logical precondition or postcondition, etc.
";


// File: classstd_1_1map.xml
%feature("docstring") std::map "

STL class. ";


// File: classXapian_1_1MatchDecider.xml
%feature("docstring") Xapian::MatchDecider "

Base class for matcher decision functor. ";

%feature("docstring")  Xapian::MatchDecider::~MatchDecider "

Destructor.

virtual Xapian::MatchDecider::~MatchDecider() ";


// File: classXapian_1_1MatchSpy.xml
%feature("docstring") Xapian::MatchSpy "

Abstract base class for match spies.

The subclasses will generally accumulate information seen during the
match, to calculate aggregate functions, or other profiles of the
matching documents. ";

%feature("docstring")  Xapian::MatchSpy::~MatchSpy "

Virtual destructor, because we have virtual methods.

virtual Xapian::MatchSpy::~MatchSpy() ";

%feature("docstring")  Xapian::MatchSpy::clone "

Clone the match spy.

virtual MatchSpy* Xapian::MatchSpy::clone() const

The clone should inherit the configuration of the parent, but need not
inherit the state. ie, the clone does not need to be passed
information about the results seen by the parent.

If you don't want to support the remote backend in your match spy, you
can use the default implementation which simply throws
Xapian::UnimplementedError.

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".
";

%feature("docstring")  Xapian::MatchSpy::name "

Return the name of this match spy.

virtual std::string Xapian::MatchSpy::name() const

This name is used by the remote backend. It is passed with the
serialised parameters to the remote server so that it knows which
class to create.

Return the full namespace-qualified name of your class here - if your
class is called MyApp::FooMatchSpy, return \"MyApp::FooMatchSpy\" from
this method.

If you don't want to support the remote backend in your match spy, you
can use the default implementation which simply throws
Xapian::UnimplementedError. ";

%feature("docstring")  Xapian::MatchSpy::serialise "

Return this object's parameters serialised as a single string.

virtual std::string Xapian::MatchSpy::serialise() const

If you don't want to support the remote backend in your match spy, you
can use the default implementation which simply throws
Xapian::UnimplementedError. ";

%feature("docstring")  Xapian::MatchSpy::unserialise "

Unserialise parameters.

virtual MatchSpy* Xapian::MatchSpy::unserialise(const std::string &s,
const Registry &context) const

This method unserialises parameters serialised by the  serialise()
method and allocates and returns a new object initialised with them.

If you don't want to support the remote backend in your match spy, you
can use the default implementation which simply throws
Xapian::UnimplementedError.

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".
";

%feature("docstring")  Xapian::MatchSpy::serialise_results "

Serialise the results of this match spy.

virtual std::string Xapian::MatchSpy::serialise_results() const

If you don't want to support the remote backend in your match spy, you
can use the default implementation which simply throws
Xapian::UnimplementedError. ";

%feature("docstring")  Xapian::MatchSpy::merge_results "

Unserialise some results, and merge them into this matchspy.

virtual void Xapian::MatchSpy::merge_results(const std::string &s)

The order in which results are merged should not be significant, since
this order is not specified (and will vary depending on the speed of
the search in each sub-database).

If you don't want to support the remote backend in your match spy, you
can use the default implementation which simply throws
Xapian::UnimplementedError. ";

%feature("docstring")  Xapian::MatchSpy::get_description "

Return a string describing this object.

virtual std::string Xapian::MatchSpy::get_description() const

This default implementation returns a generic answer, to avoid forcing
those deriving their own MatchSpy subclasses from having to implement
this (they may not care what get_description() gives for their
subclass). ";


// File: classXapian_1_1MSet.xml
%feature("docstring") Xapian::MSet "

A match set ( MSet).

This class represents (a portion of) the results of a query. ";

%feature("docstring")  Xapian::MSet::MSet "Xapian::MSet::MSet(MSet::Internal *internal_) ";

%feature("docstring")  Xapian::MSet::MSet "

Create an empty Xapian::MSet.

Xapian::MSet::MSet() ";

%feature("docstring")  Xapian::MSet::~MSet "

Destroy a Xapian::MSet.

Xapian::MSet::~MSet() ";

%feature("docstring")  Xapian::MSet::MSet "

Copying is allowed (and is cheap).

Xapian::MSet::MSet(const MSet &other) ";

%feature("docstring")  Xapian::MSet::fetch "

Fetch the document info for a set of items in the MSet.

void Xapian::MSet::fetch(const MSetIterator &begin, const MSetIterator
&end) const

This method causes the documents in the range specified by the
iterators to be fetched from the database, and cached in the
Xapian::MSet object. This has little effect when performing a search
across a local database, but will greatly speed up subsequent access
to the document contents when the documents are stored in a remote
database.

The iterators must be over this Xapian::MSet - undefined behaviour
will result otherwise.

Parameters:
-----------

begin:   MSetIterator for first item to fetch.

end:   MSetIterator for item after last item to fetch. ";

%feature("docstring")  Xapian::MSet::fetch "

Fetch the single item specified.

void Xapian::MSet::fetch(const MSetIterator &item) const ";

%feature("docstring")  Xapian::MSet::fetch "

Fetch all the items in the MSet.

void Xapian::MSet::fetch() const ";

%feature("docstring")  Xapian::MSet::convert_to_percent "

This converts the weight supplied to a percentage score.

Xapian::percent Xapian::MSet::convert_to_percent(Xapian::weight wt)
const

The return value will be in the range 0 to 100, and will be 0 if and
only if the item did not match the query at all. ";

%feature("docstring")  Xapian::MSet::convert_to_percent "

Return the percentage score for a particular item.

Xapian::percent Xapian::MSet::convert_to_percent(const MSetIterator
&it) const ";

%feature("docstring")  Xapian::MSet::get_termfreq "

Return the term frequency of the given query term.

Xapian::doccount Xapian::MSet::get_termfreq(const std::string &tname)
const

Parameters:
-----------

tname:  The term to look for.

This is sometimes more efficient than asking the database directly for
the term frequency - in particular, if the term was in the query, its
frequency will usually be cached in the MSet. ";

%feature("docstring")  Xapian::MSet::get_termweight "

Return the term weight of the given query term.

Xapian::weight Xapian::MSet::get_termweight(const std::string &tname)
const

Parameters:
-----------

tname:  The term to look for.

Parameters:
-----------

Xapian::InvalidArgumentError:  is thrown if the term was not in the
query. ";

%feature("docstring")  Xapian::MSet::get_firstitem "

The index of the first item in the result which was put into the MSet.

Xapian::doccount Xapian::MSet::get_firstitem() const

This corresponds to the parameter \"first\" specified in
Xapian::Enquire::get_mset(). A value of 0 corresponds to the highest
result being the first item in the MSet. ";

%feature("docstring")  Xapian::MSet::get_matches_lower_bound "

A lower bound on the number of documents in the database which match
the query.

Xapian::doccount Xapian::MSet::get_matches_lower_bound() const

This figure takes into account collapsing of duplicates, and weighting
cutoff values.

This number is usually considerably less than the actual number of
documents which match the query. ";

%feature("docstring")  Xapian::MSet::get_matches_estimated "

An estimate for the number of documents in the database which match
the query.

Xapian::doccount Xapian::MSet::get_matches_estimated() const

This figure takes into account collapsing of duplicates, and weighting
cutoff values.

This value is returned because there is sometimes a request to display
such information. However, our experience is that presenting this
value to users causes them to worry about the large number of results,
rather than how useful those at the top of the result set are, and is
thus undesirable. ";

%feature("docstring")  Xapian::MSet::get_matches_upper_bound "

An upper bound on the number of documents in the database which match
the query.

Xapian::doccount Xapian::MSet::get_matches_upper_bound() const

This figure takes into account collapsing of duplicates, and weighting
cutoff values.

This number is usually considerably greater than the actual number of
documents which match the query. ";

%feature("docstring")
Xapian::MSet::get_uncollapsed_matches_lower_bound "

A lower bound on the number of documents in the database which would
match the query if collapsing wasn't used.

Xapian::doccount Xapian::MSet::get_uncollapsed_matches_lower_bound()
const ";

%feature("docstring")  Xapian::MSet::get_uncollapsed_matches_estimated
"

A estimate of the number of documents in the database which would
match the query if collapsing wasn't used.

Xapian::doccount Xapian::MSet::get_uncollapsed_matches_estimated()
const ";

%feature("docstring")
Xapian::MSet::get_uncollapsed_matches_upper_bound "

A upper bound on the number of documents in the database which would
match the query if collapsing wasn't used.

Xapian::doccount Xapian::MSet::get_uncollapsed_matches_upper_bound()
const ";

%feature("docstring")  Xapian::MSet::get_max_possible "

The maximum possible weight in the MSet.

Xapian::weight Xapian::MSet::get_max_possible() const

This weight is likely not to be attained in the set of results, but
represents an upper bound on the weight which a document could attain
for the given query. ";

%feature("docstring")  Xapian::MSet::get_max_attained "

The greatest weight which is attained by any document in the database.

Xapian::weight Xapian::MSet::get_max_attained() const

If firstitem == 0 and the primary ordering is by relevance, this is
the weight of the first entry in the MSet.

If no documents are found by the query, this will be 0.

Note that calculation of max_attained requires calculation of at least
one result item - therefore, if no items were requested when the query
was performed (by specifying maxitems = 0 in
Xapian::Enquire::get_mset()), this value will be 0. ";

%feature("docstring")  Xapian::MSet::size "

The number of items in this MSet.

Xapian::doccount Xapian::MSet::size() const ";

%feature("docstring")  Xapian::MSet::max_size "

Required to allow use as an STL container.

Xapian::doccount Xapian::MSet::max_size() const ";

%feature("docstring")  Xapian::MSet::empty "

Test if this MSet is empty.

bool Xapian::MSet::empty() const ";

%feature("docstring")  Xapian::MSet::swap "

Swap the MSet we point to with another.

void Xapian::MSet::swap(MSet &other) ";

%feature("docstring")  Xapian::MSet::begin "

Iterator for the items in this MSet.

MSetIterator Xapian::MSet::begin() const ";

%feature("docstring")  Xapian::MSet::end "

End iterator corresponding to begin().

MSetIterator Xapian::MSet::end() const ";

%feature("docstring")  Xapian::MSet::back "

Iterator pointing to the last element of this MSet.

MSetIterator Xapian::MSet::back() const ";

%feature("docstring")  Xapian::MSet::get_description "

Return a string describing this object.

std::string Xapian::MSet::get_description() const ";


// File: classXapian_1_1MSetIterator.xml
%feature("docstring") Xapian::MSetIterator "

An iterator pointing to items in an MSet.

This is used for access to individual results of a match. ";

%feature("docstring")  Xapian::MSetIterator::MSetIterator "

Create an uninitialised iterator; this cannot be used, but is
convenient syntactically.

Xapian::MSetIterator::MSetIterator() ";

%feature("docstring")  Xapian::MSetIterator::MSetIterator "

Copying is allowed (and is cheap).

Xapian::MSetIterator::MSetIterator(const MSetIterator &other) ";

%feature("docstring")  Xapian::MSetIterator::get_document "

Get a Xapian::Document object for the current position.

Xapian::Document Xapian::MSetIterator::get_document() const

This method returns a Xapian::Document object which provides the
information about the document pointed to by the MSetIterator.

If the underlying database has suitable support, using this call
(rather than asking the database for a document based on its document
ID) will enable the system to ensure that the correct data is
returned, and that the document has not been deleted or changed since
the query was performed.

A Xapian::Document object containing the document data.

Parameters:
-----------

Xapian::DocNotFoundError:  The document specified could not be found
in the database. ";

%feature("docstring")  Xapian::MSetIterator::get_rank "

Get the rank of the document at the current position.

Xapian::doccount Xapian::MSetIterator::get_rank() const

The rank is the position that this document is at in the ordered list
of results of the query. The result is 0-based - i.e. the top-ranked
document has a rank of 0. ";

%feature("docstring")  Xapian::MSetIterator::get_weight "

Get the weight of the document at the current position.

Xapian::weight Xapian::MSetIterator::get_weight() const ";

%feature("docstring")  Xapian::MSetIterator::get_collapse_key "

Get the collapse key for this document.

std::string Xapian::MSetIterator::get_collapse_key() const ";

%feature("docstring")  Xapian::MSetIterator::get_collapse_count "

Get an estimate of the number of documents that have been collapsed
into this one.

Xapian::doccount Xapian::MSetIterator::get_collapse_count() const

The estimate will always be less than or equal to the actual number of
other documents satisfying the match criteria with the same collapse
key as this document.

This method may return 0 even though there are other documents with
the same collapse key which satisfying the match criteria. However if
this method returns non-zero, there definitely are other such
documents. So this method may be used to inform the user that there
are \"at least N other matches in this group\", or to control whether
to offer a \"show other documents in this group\" feature (but note
that it may not offer it in every case where it would show other
documents). ";

%feature("docstring")  Xapian::MSetIterator::get_percent "

This returns the weight of the document as a percentage score.

Xapian::percent Xapian::MSetIterator::get_percent() const

The return value will be an integer in the range 0 to 100: 0 meaning
that the item did not match the query at all.

The intention is that the highest weighted document will get 100 if it
matches all the weight-contributing terms in the query. However,
currently it may get a lower percentage score if you use a
MatchDecider and the sorting is primarily by value. In this case, the
percentage for a particular document may vary depending on the first,
max_size, and checkatleast parameters passed to Enquire::get_mset()
(this bug is hard to fix without having to apply the MatchDecider to
potentially many more documents, which is potentially costly). ";

%feature("docstring")  Xapian::MSetIterator::get_description "

Return a string describing this object.

std::string Xapian::MSetIterator::get_description() const ";


// File: classstd_1_1multimap.xml
%feature("docstring") std::multimap "

STL class. ";


// File: classstd_1_1multiset.xml
%feature("docstring") std::multiset "

STL class. ";


// File: classXapian_1_1MultiValueKeyMaker.xml
%feature("docstring") Xapian::MultiValueKeyMaker "

KeyMaker subclass which combines several values.

When the result is used for sorting, results are ordered by the first
value. In the event of a tie, the second is used. If this is the same
for both, the third is used, and so on. If reverse is true for a
value, then the sort order for that value is reversed.

When used for collapsing, the documents will only be considered equal
if all the values specified match. If none of the specified values are
set then the generated key will be empty, so such documents won't be
collapsed (which is consistent with the behaviour in the \"collapse on
a value\" case). If you'd prefer that documents with none of the keys
set are collapsed together, then you can set reverse for at least one
of the values. Other than this, it isn't useful to set reverse for
collapsing. ";

%feature("docstring")  Xapian::MultiValueKeyMaker::MultiValueKeyMaker
"Xapian::MultiValueKeyMaker::MultiValueKeyMaker() ";

%feature("docstring")  Xapian::MultiValueKeyMaker::MultiValueKeyMaker
"Xapian::MultiValueKeyMaker::MultiValueKeyMaker(Iterator begin,
Iterator end) ";

%feature("docstring")  Xapian::MultiValueKeyMaker::add_value "void
Xapian::MultiValueKeyMaker::add_value(Xapian::valueno slot, bool
reverse=false) ";


// File: classXapian_1_1MultiValueSorter.xml
%feature("docstring") Xapian::MultiValueSorter "

Sorter subclass which sorts by a several values.

Results are ordered by the first value. In the event of a tie, the
second is used. If this is the same for both, the third is used, and
so on.

Deprecated This class is deprecated - you should migrate to using
MultiValueKeyMaker instead. Note that MultiValueSorter::add() becomes
MultiValueKeyMaker::add_value(), but the sense of the direction flag
is reversed (to be consistent with Enquire::set_sort_by_value()), so:
MultiValueSorter sorter; // Primary ordering is forwards on value 4.
sorter.add(4); // Secondary ordering is reverse on value 5.
sorter.add(5, false);

becomes:

MultiValueKeyMaker sorter; // Primary ordering is forwards on value 4.
sorter.add_value(4); // Secondary ordering is reverse on value 5.
sorter.add_value(5, true); ";

%feature("docstring")  Xapian::MultiValueSorter::MultiValueSorter "Xapian::MultiValueSorter::MultiValueSorter() ";

%feature("docstring")  Xapian::MultiValueSorter::MultiValueSorter "Xapian::MultiValueSorter::MultiValueSorter(Iterator begin, Iterator
end) ";

%feature("docstring")  Xapian::MultiValueSorter::add "void
Xapian::MultiValueSorter::add(Xapian::valueno slot, bool forward=true)
";


// File: classXapian_1_1NetworkError.xml
%feature("docstring") Xapian::NetworkError "

Indicates a problem communicating with a remote database. ";

%feature("docstring")  Xapian::NetworkError::NetworkError "

General purpose constructor which allows setting errno.

Xapian::NetworkError::NetworkError(const std::string &msg_, const
std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")  Xapian::NetworkError::NetworkError "

Construct from message and errno value.

Xapian::NetworkError::NetworkError(const std::string &msg_, int
errno_) ";


// File: classXapian_1_1NetworkTimeoutError.xml
%feature("docstring") Xapian::NetworkTimeoutError "

Indicates a timeout expired while communicating with a remote
database. ";

%feature("docstring")
Xapian::NetworkTimeoutError::NetworkTimeoutError "

General purpose constructor which allows setting errno.

Xapian::NetworkTimeoutError::NetworkTimeoutError(const std::string
&msg_, const std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")
Xapian::NetworkTimeoutError::NetworkTimeoutError "

Construct from message and errno value.

Xapian::NetworkTimeoutError::NetworkTimeoutError(const std::string
&msg_, int errno_) ";


// File: classXapian_1_1NumberValueRangeProcessor.xml
%feature("docstring") Xapian::NumberValueRangeProcessor "

Handle a number range.

This class must be used on values which have been encoded using
Xapian::sortable_serialise() which turns numbers into strings which
will sort in the same order as the numbers (the same values can be
used to implement a numeric sort). ";

%feature("docstring")
Xapian::NumberValueRangeProcessor::NumberValueRangeProcessor "

Constructor.

Xapian::NumberValueRangeProcessor::NumberValueRangeProcessor(Xapian::valueno
slot_)

Parameters:
-----------

slot_:  The value number to return from operator(). ";

%feature("docstring")
Xapian::NumberValueRangeProcessor::NumberValueRangeProcessor "

Constructor.

Xapian::NumberValueRangeProcessor::NumberValueRangeProcessor(Xapian::valueno
slot_, const std::string &str_, bool prefix_=true)

Parameters:
-----------

slot_:  The value number to return from operator().

str_:  A string to look for to recognise values as belonging to this
numeric range.

prefix_:  Whether to look for the string at the start or end of the
values. If true, the string is a prefix; if false, the string is a
suffix (default: true).

The string supplied in str_ is used by operator() to decide whether
the pair of strings supplied to it constitute a valid range. If
prefix_ is true, the first value in a range must begin with str_ (and
the second value may optionally begin with str_); if prefix_ is false,
the second value in a range must end with str_ (and the first value
may optionally end with str_).

If str_ is empty, the setting of prefix_ is irrelevant, and no special
strings are required at the start or end of the strings defining the
range.

The remainder of both strings defining the endpoints must be valid
floating point numbers. (FIXME: define format recognised).

For example, if str_ is \"$\" and prefix_ is true, and the range
processor has been added to the queryparser, the queryparser will
accept \"$10..50\" or \"$10..$50\", but not \"10..50\" or \"10..$50\"
as valid ranges. If str_ is \"kg\" and prefix_ is false, the
queryparser will accept \"10..50kg\" or \"10kg..50kg\", but not
\"10..50\" or \"10kg..50\" as valid ranges. ";


// File: classstd_1_1ofstream.xml
%feature("docstring") std::ofstream "

STL class. ";


// File: classstd_1_1ostream.xml
%feature("docstring") std::ostream "

STL class. ";


// File: classstd_1_1ostringstream.xml
%feature("docstring") std::ostringstream "

STL class. ";


// File: classstd_1_1out__of__range.xml
%feature("docstring") std::out_of_range "

STL class. ";


// File: classstd_1_1overflow__error.xml
%feature("docstring") std::overflow_error "

STL class. ";


// File: classXapian_1_1PositionIterator.xml
%feature("docstring") Xapian::PositionIterator "

An iterator pointing to items in a list of positions. ";

%feature("docstring")  Xapian::PositionIterator::PositionIterator "Xapian::PositionIterator::PositionIterator(Internal *internal_) ";

%feature("docstring")  Xapian::PositionIterator::PositionIterator "

Default constructor - for declaring an uninitialised iterator.

Xapian::PositionIterator::PositionIterator() ";

%feature("docstring")  Xapian::PositionIterator::~PositionIterator "

Destructor.

Xapian::PositionIterator::~PositionIterator() ";

%feature("docstring")  Xapian::PositionIterator::PositionIterator "

Copying is allowed.

Xapian::PositionIterator::PositionIterator(const PositionIterator &o)

The internals are reference counted, so copying is also cheap. ";

%feature("docstring")  Xapian::PositionIterator::skip_to "

Advance the iterator to the specified termpos.

void Xapian::PositionIterator::skip_to(Xapian::termpos pos)

If the specified termpos isn't in the list, position ourselves on the
first termpos after it (or at_end() if no greater term positions are
present). ";

%feature("docstring")  Xapian::PositionIterator::get_description "

Return a string describing this object.

std::string Xapian::PositionIterator::get_description() const ";


// File: classXapian_1_1PostingIterator.xml
%feature("docstring") Xapian::PostingIterator "

An iterator pointing to items in a list of postings. ";

%feature("docstring")  Xapian::PostingIterator::PostingIterator "

Default constructor - for declaring an uninitialised iterator.

Xapian::PostingIterator::PostingIterator() ";

%feature("docstring")  Xapian::PostingIterator::~PostingIterator "

Destructor.

Xapian::PostingIterator::~PostingIterator() ";

%feature("docstring")  Xapian::PostingIterator::PostingIterator "

Copying is allowed.

Xapian::PostingIterator::PostingIterator(const PostingIterator &other)

The internals are reference counted, so copying is also cheap. ";

%feature("docstring")  Xapian::PostingIterator::skip_to "

Advance the iterator to the specified docid.

void Xapian::PostingIterator::skip_to(Xapian::docid did)

If the specified docid isn't in the list, position ourselves on the
first document after it (or at_end() if no greater docids are
present). ";

%feature("docstring")  Xapian::PostingIterator::get_doclength "

Get the length of the document at the current position in the
postlist.

Xapian::termcount Xapian::PostingIterator::get_doclength() const

This information may be stored in the postlist, in which case this
lookup should be extremely fast (indeed, not require further disk
access). If the information is not present in the postlist, it will be
retrieved from the database, at a greater performance cost. ";

%feature("docstring")  Xapian::PostingIterator::get_wdf "

Get the within document frequency of the document at the current
position in the postlist.

Xapian::termcount Xapian::PostingIterator::get_wdf() const ";

%feature("docstring")  Xapian::PostingIterator::positionlist_begin "

Return PositionIterator pointing to start of positionlist for current
document.

PositionIterator Xapian::PostingIterator::positionlist_begin() const
";

%feature("docstring")  Xapian::PostingIterator::positionlist_end "

Return PositionIterator pointing to end of positionlist for current
document.

PositionIterator Xapian::PostingIterator::positionlist_end() const ";

%feature("docstring")  Xapian::PostingIterator::get_description "

Return a string describing this object.

std::string Xapian::PostingIterator::get_description() const ";


// File: classXapian_1_1PostingSource.xml
%feature("docstring") Xapian::PostingSource "

Base class which provides an \"external\" source of postings. ";

%feature("docstring")  Xapian::PostingSource::~PostingSource "virtual
Xapian::PostingSource::~PostingSource() ";

%feature("docstring")  Xapian::PostingSource::get_termfreq_min "

A lower bound on the number of documents this object can return.

virtual Xapian::doccount Xapian::PostingSource::get_termfreq_min()
const =0

Xapian will always call init() on a PostingSource before calling this
for the first time. ";

%feature("docstring")  Xapian::PostingSource::get_termfreq_est "

An estimate of the number of documents this object can return.

virtual Xapian::doccount Xapian::PostingSource::get_termfreq_est()
const =0

It must always be true that:

get_termfreq_min() <= get_termfreq_est() <= get_termfreq_max()

Xapian will always call init() on a PostingSource before calling this
for the first time. ";

%feature("docstring")  Xapian::PostingSource::get_termfreq_max "

An upper bound on the number of documents this object can return.

virtual Xapian::doccount Xapian::PostingSource::get_termfreq_max()
const =0

Xapian will always call init() on a PostingSource before calling this
for the first time. ";

%feature("docstring")  Xapian::PostingSource::get_maxweight "

Return the currently set upper bound on what get_weight() can return.

Xapian::weight Xapian::PostingSource::get_maxweight() const ";

%feature("docstring")  Xapian::PostingSource::get_weight "

Return the weight contribution for the current document.

virtual Xapian::weight Xapian::PostingSource::get_weight() const

This default implementation always returns 0, for convenience when
implementing \"weight-less\" PostingSource subclasses.

This method may assume that it will only be called when there is a
\"current document\". In detail: Xapian will always call init() on a
PostingSource before calling this for the first time. It will also
only call this if the PostingSource reports that it is pointing to a
valid document (ie, it will not call it before calling at least one of
next(), skip_to() or check(), and will ensure that the PostingSource
is not at the end by calling at_end()). ";

%feature("docstring")  Xapian::PostingSource::get_docid "

Return the current docid.

virtual Xapian::docid Xapian::PostingSource::get_docid() const =0

This method may assume that it will only be called when there is a
\"current document\". See  get_weight() for details.

Note: in the case of a multi-database search, the returned docid
should be in the single subdatabase relevant to this posting source.
See the  init() method for details. ";

%feature("docstring")  Xapian::PostingSource::next "

Advance the current position to the next matching document.

virtual void Xapian::PostingSource::next(Xapian::weight min_wt)=0

The PostingSource starts before the first entry in the list, so next()
must be called before any methods which need the context of the
current position.

Xapian will always call init() on a PostingSource before calling this
for the first time.

Parameters:
-----------

min_wt:  The minimum weight contribution that is needed (this is just
a hint which subclasses may ignore). ";

%feature("docstring")  Xapian::PostingSource::skip_to "

Advance to the specified docid.

virtual void Xapian::PostingSource::skip_to(Xapian::docid did,
Xapian::weight min_wt)

If the specified docid isn't in the list, position ourselves on the
first document after it (or at_end() if no greater docids are
present).

If the current position is already the specified docid, this method
will leave the position unmodified.

If the specified docid is earlier than the current position, the
behaviour is unspecified. A sensible behaviour would be to leave the
current position unmodified, but it is also reasonable to move to the
specified docid.

The default implementation calls next() repeatedly, which works but
skip_to() can often be implemented much more efficiently.

Xapian will always call init() on a PostingSource before calling this
for the first time.

Note: in the case of a multi-database search, the docid specified is
the docid in the single subdatabase relevant to this posting source.
See the  init() method for details.

Parameters:
-----------

min_wt:  The minimum weight contribution that is needed (this is just
a hint which subclasses may ignore). ";

%feature("docstring")  Xapian::PostingSource::check "

Check if the specified docid occurs.

virtual bool Xapian::PostingSource::check(Xapian::docid did,
Xapian::weight min_wt)

The caller is required to ensure that the specified document id did
actually exists in the database. If it does, it must move to that
document id, and return true. If it does not, it may either:

return true, having moved to a definite position (including
\"at_end\"), which must be the same position as skip_to() would have
moved to.

or

return false, having moved to an \"indeterminate\" position, such that
a subsequent call to next() or skip_to() will move to the next
matching position after did.

Generally, this method should act like skip_to() and return true if
that can be done at little extra cost.

Otherwise it should simply check if a particular docid is present,
returning true if it is, and false if it isn't.

The default implementation calls skip_to() and always returns true.

Xapian will always call init() on a PostingSource before calling this
for the first time.

Note: in the case of a multi-database search, the docid specified is
the docid in the single subdatabase relevant to this posting source.
See the  init() method for details. ";

%feature("docstring")  Xapian::PostingSource::at_end "

Return true if the current position is past the last entry in this
list.

virtual bool Xapian::PostingSource::at_end() const =0

At least one of  next(),  skip_to() or  check() will be called before
this method is first called. ";

%feature("docstring")  Xapian::PostingSource::clone "

Clone the posting source.

virtual PostingSource* Xapian::PostingSource::clone() const

The clone should inherit the configuration of the parent, but need not
inherit the state. ie, the clone does not need to be in the same
iteration position as the original: the matcher will always call
init() on the clone before attempting to move the iterator, or read
the information about the current position of the iterator.

This may return NULL to indicate that cloning is not supported. In
this case, the PostingSource may only be used with a single-database
search.

The default implementation returns NULL.

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".
";

%feature("docstring")  Xapian::PostingSource::name "

Name of the posting source class.

virtual std::string Xapian::PostingSource::name() const

This is used when serialising and unserialising posting sources; for
example, for performing remote searches.

If the subclass is in a C++ namespace, the namespace should be
included in the name, using \"::\" as a separator. For example, for a
PostingSource subclass called \"FooPostingSource\" in the \"Xapian\"
namespace the result of this call should be
\"Xapian::FooPostingSource\".

This should only be implemented if serialise() and unserialise() are
also implemented. The default implementation returns an empty string.

If this returns an empty string, Xapian will assume that serialise()
and unserialise() are not implemented. ";

%feature("docstring")  Xapian::PostingSource::serialise "

Serialise object parameters into a string.

virtual std::string Xapian::PostingSource::serialise() const

The serialised parameters should represent the configuration of the
posting source, but need not (indeed, should not) represent the
current iteration state.

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.
";

%feature("docstring")  Xapian::PostingSource::unserialise "

Create object given string serialisation returned by serialise().

virtual PostingSource* Xapian::PostingSource::unserialise(const
std::string &s) const

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.

Parameters:
-----------

s:  A serialised instance of this PostingSource subclass. ";

%feature("docstring")  Xapian::PostingSource::init "

Set this PostingSource to the start of the list of postings.

virtual void Xapian::PostingSource::init(const Database &db)=0

This is called automatically by the matcher prior to each query being
processed.

If a PostingSource is used for multiple searches,  init() will
therefore be called multiple times, and must handle this by using the
database passed in the most recent call.

Parameters:
-----------

db:  The database which the PostingSource should iterate through.

Note: the database supplied to this method must not be modified: in
particular, the reopen() method should not be called on it.

Note: in the case of a multi-database search, a separate PostingSource
will be used for each database (the separate PostingSources will be
obtained using  clone()), and each PostingSource will be passed one of
the sub-databases as the db parameter here. The db parameter will
therefore always refer to a single database. All docids passed to, or
returned from, the PostingSource refer to docids in that single
database, rather than in the multi- database. ";

%feature("docstring")  Xapian::PostingSource::get_description "

Return a string describing this object.

virtual std::string Xapian::PostingSource::get_description() const

This default implementation returns a generic answer. This default it
provided to avoid forcing those deriving their own PostingSource
subclass from having to implement this (they may not care what
get_description() gives for their subclass). ";


// File: classstd_1_1priority__queue.xml
%feature("docstring") std::priority_queue "

STL class. ";


// File: classXapian_1_1Query.xml
%feature("docstring") Xapian::Query "

Class representing a query.

Queries are represented as a tree of objects. ";

%feature("docstring")  Xapian::Query::Query "

Copy constructor.

Xapian::Query::Query(const Query &copyme) ";

%feature("docstring")  Xapian::Query::Query "

Default constructor: makes an empty query which matches no documents.

Xapian::Query::Query()

Also useful for defining a Query object to be assigned to later.

An exception will be thrown if an attempt is made to use an undefined
query when building up a composite query. ";

%feature("docstring")  Xapian::Query::~Query "

Destructor.

Xapian::Query::~Query() ";

%feature("docstring")  Xapian::Query::Query "

A query consisting of a single term.

Xapian::Query::Query(const std::string &tname_, Xapian::termcount
wqf_=1, Xapian::termpos pos_=0) ";

%feature("docstring")  Xapian::Query::Query "

A query consisting of two subqueries, opp-ed together.

Xapian::Query::Query(Query::op op_, const Query &left, const Query
&right) ";

%feature("docstring")  Xapian::Query::Query "

A query consisting of two termnames opp-ed together.

Xapian::Query::Query(Query::op op_, const std::string &left, const
std::string &right) ";

%feature("docstring")  Xapian::Query::Query "

Combine a number of Xapian::Query-s with the specified operator.

Xapian::Query::Query(Query::op op_, Iterator qbegin, Iterator qend,
Xapian::termcount parameter=0)

The Xapian::Query objects are specified with begin and end iterators.

AND, OR, SYNONYM, NEAR and PHRASE can take any number of subqueries.
Other operators take exactly two subqueries.

The iterators may be to Xapian::Query objects, pointers to
Xapian::Query objects, or termnames (std::string-s).

For NEAR and PHRASE, a window size can be specified in parameter.

For ELITE_SET, the elite set size can be specified in parameter. ";

%feature("docstring")  Xapian::Query::Query "

Apply the specified operator to a single Xapian::Query object, with a
double parameter.

Xapian::Query::Query(Query::op op_, Xapian::Query q, double parameter)
";

%feature("docstring")  Xapian::Query::Query "

Construct a value range query on a document value.

Xapian::Query::Query(Query::op op_, Xapian::valueno slot, const
std::string &begin, const std::string &end)

A value range query matches those documents which have a value stored
in the slot given by slot which is in the range specified by begin and
end (in lexicographical order), including the endpoints.

Parameters:
-----------

op_:  The operator to use for the query. Currently, must be
OP_VALUE_RANGE.

slot:  The slot number to get the value from.

begin:  The start of the range.

end:  The end of the range. ";

%feature("docstring")  Xapian::Query::Query "

Construct a value comparison query on a document value.

Xapian::Query::Query(Query::op op_, Xapian::valueno slot, const
std::string &value)

This query matches those documents which have a value stored in the
slot given by slot which compares, as specified by the operator, to
value.

Parameters:
-----------

op_:  The operator to use for the query. Currently, must be
OP_VALUE_GE or OP_VALUE_LE.

slot:  The slot number to get the value from.

value:  The value to compare. ";

%feature("docstring")  Xapian::Query::Query "

Construct an external source query.

Xapian::Query::Query(Xapian::PostingSource *external_source)

An attempt to clone the posting source will be made immediately, so if
the posting source supports clone(), the source supplied may be safely
deallocated after this call. If the source does not support clone(),
the caller must ensure that the posting source remains valid until the
Query is deallocated.

Parameters:
-----------

external_source:  The source to use in the query. ";

%feature("docstring")  Xapian::Query::get_length "

Get the length of the query, used by some ranking formulae.

Xapian::termcount Xapian::Query::get_length() const

This value is calculated automatically - if you want to override it
you can pass a different value to Enquire::set_query(). ";

%feature("docstring")  Xapian::Query::get_terms_begin "

Return a Xapian::TermIterator returning all the terms in the query, in
order of termpos.

TermIterator Xapian::Query::get_terms_begin() const

If multiple terms have the same term position, their order is
unspecified. Duplicates (same term and termpos) will be removed. ";

%feature("docstring")  Xapian::Query::get_terms_end "

Return a Xapian::TermIterator to the end of the list of terms in the
query.

TermIterator Xapian::Query::get_terms_end() const ";

%feature("docstring")  Xapian::Query::empty "

Test if the query is empty (i.e.

bool Xapian::Query::empty() const

was constructed using the default ctor or with an empty iterator
ctor). ";

%feature("docstring")  Xapian::Query::serialise "

Serialise query into a string.

std::string Xapian::Query::serialise() const

The query representation may change between Xapian releases: even
between minor versions. However, it is guaranteed not to change unless
the remote database protocol has also changed between releases. ";

%feature("docstring")  Xapian::Query::get_description "

Return a string describing this object.

std::string Xapian::Query::get_description() const ";


// File: classXapian_1_1QueryParser.xml
%feature("docstring") Xapian::QueryParser "

Build a Xapian::Query object from a user query string. ";

%feature("docstring")  Xapian::QueryParser::QueryParser "

Copy constructor.

Xapian::QueryParser::QueryParser(const QueryParser &o) ";

%feature("docstring")  Xapian::QueryParser::QueryParser "

Default constructor.

Xapian::QueryParser::QueryParser() ";

%feature("docstring")  Xapian::QueryParser::~QueryParser "

Destructor.

Xapian::QueryParser::~QueryParser() ";

%feature("docstring")  Xapian::QueryParser::set_stemmer "

Set the stemmer.

void Xapian::QueryParser::set_stemmer(const Xapian::Stem &stemmer)

This sets the stemming algorithm which will be used by the query
parser. Note that the stemming algorithm will only be used according
to the stemming strategy set by set_stemming_strategy(), which
defaults to STEM_NONE. Therefore, to use a stemming algorithm, you
will also need to call set_stemming_strategy() with a value other than
STEM_NONE. ";

%feature("docstring")  Xapian::QueryParser::set_stemming_strategy "

Set the stemming strategy.

void Xapian::QueryParser::set_stemming_strategy(stem_strategy
strategy)

This controls how the query parser will apply the stemming algorithm.
The default value is STEM_NONE. The possible values are:

STEM_NONE: Don't perform any stemming.

STEM_SOME: Search for stemmed forms of terms except for those which
start with a capital letter, or are followed by certain characters
(currently: (/@<>=*[{\" ), or are used with operators which need
positional information. Stemmed terms are prefixed with 'Z'.

STEM_ALL: Search for stemmed forms of all words (note: no 'Z' prefix
is added).

Note that the stemming algorithm is only applied to words in
probabilistic fields - boolean filter terms are never stemmed. ";

%feature("docstring")  Xapian::QueryParser::set_stopper "

Set the stopper.

void Xapian::QueryParser::set_stopper(const Stopper *stop=NULL) ";

%feature("docstring")  Xapian::QueryParser::set_default_op "

Set the default operator.

void Xapian::QueryParser::set_default_op(Query::op default_op)

This operator is used to combine non-filter query items when no
explicit operator is used.

The most useful values for this are OP_OR (the default) and OP_AND.
OP_NEAR and OP_PHRASE can also be useful.

So for example, 'weather forecast' is parsed as if it were 'weather OR
forecast' by default. ";

%feature("docstring")  Xapian::QueryParser::get_default_op "

Get the current default operator.

Query::op Xapian::QueryParser::get_default_op() const ";

%feature("docstring")  Xapian::QueryParser::set_database "

Specify the database being searched.

void Xapian::QueryParser::set_database(const Database &db)

The database is used for wildcard expansion (FLAG_WILDCARD and
FLAG_PARTIAL), spelling correction (FLAG_SPELLING_CORRECTION), and
synonyms (FLAG_SYNONYM, FLAG_AUTO_SYNONYMS, and
FLAG_AUTO_MULTIWORD_SYNONYMS). ";

%feature("docstring")  Xapian::QueryParser::set_max_wildcard_expansion
"

Specify the maximum expansion of a wildcard term.

void Xapian::QueryParser::set_max_wildcard_expansion(Xapian::termcount
limit)

Note: you must also set FLAG_WILDCARD for wildcard expansion to
happen.

Parameters:
-----------

limit:  The maximum number of terms each wildcard in the query can
expand to, or 0 for no limit (which is the default). ";

%feature("docstring")  Xapian::QueryParser::parse_query "

Parse a query.

Query Xapian::QueryParser::parse_query(const std::string
&query_string, unsigned flags=FLAG_DEFAULT, const std::string
&default_prefix=std::string())

Parameters:
-----------

query_string:  A free-text query as entered by a user

flags:  Zero or more Query::feature_flag specifying what features the
QueryParser should support. Combine multiple values with bitwise-or
(|) (default FLAG_DEFAULT).

default_prefix:  The default term prefix to use (default none). For
example, you can pass \"A\" when parsing an \"Author\" field.

Parameters:
-----------

If:  the query string can't be parsed, then Xapian::QueryParserError
is thrown. You can get an English error message to report to the user
by catching it and calling get_msg() on the caught exception. The
current possible values (in case you want to translate them) are:

Unknown range operation

parse error

Syntax: <expression> AND <expression>

Syntax: <expression> AND NOT <expression>

Syntax: <expression> NOT <expression>

Syntax: <expression> OR <expression>

Syntax: <expression> XOR <expression> ";

%feature("docstring")  Xapian::QueryParser::add_prefix "

Add a probabilistic term prefix.

void Xapian::QueryParser::add_prefix(const std::string &field, const
std::string &prefix)

For example:

This allows the user to search for author:Orwell which will be
converted to a search for the term \"Aorwell\".

Multiple fields can be mapped to the same prefix. For example, you can
make title: and subject: aliases for each other.

As of 1.0.4, you can call this method multiple times with the same
value of field to allow a single field to be mapped to multiple
prefixes. Multiple terms being generated for such a field, and
combined with  Xapian::Query::OP_OR.

If any prefixes are specified for the empty field name (i.e. you call
this method with an empty string as the first parameter) these
prefixes will be used for terms without a field specifier. If you do
this and also specify the default_prefix parameter to  parse_query(),
then the default_prefix parameter will override.

If the prefix parameter is empty, then \"field:word\" will produce the
term \"word\" (and this can be one of several prefixes for a
particular field, or for terms without a field specifier).

If you call  add_prefix() and  add_boolean_prefix() for the same value
of field, a  Xapian::InvalidOperationError exception will be thrown.

In 1.0.3 and earlier, subsequent calls to this method with the same
value of field had no effect.

Parameters:
-----------

field:  The user visible field name

prefix:  The term prefix to map this to ";

%feature("docstring")  Xapian::QueryParser::add_boolean_prefix "

Add a boolean term prefix allowing the user to restrict a search with
a boolean filter specified in the free text query.

void Xapian::QueryParser::add_boolean_prefix(const std::string &field,
const std::string &prefix, bool exclusive)

For example:

This allows the user to restrict a search with site:xapian.org which
will be converted to Hxapian.org combined with any probabilistic query
with  Xapian::Query::OP_FILTER.

If multiple boolean filters are specified in a query for the same
prefix, they will be combined with the  Xapian::Query::OP_OR operator.
Then, if there are boolean filters for different prefixes, they will
be combined with the  Xapian::Query::OP_AND operator.

Multiple fields can be mapped to the same prefix (so for example you
can make site: and domain: aliases for each other). Instances of
fields with different aliases but the same prefix will still be
combined with the OR operator.

For example, if \"site\" and \"domain\" map to \"H\", but author maps
to \"A\", a search for \"site:foo domain:bar author:Fred\" will map to
\"(Hfoo OR Hbar) AND Afred\".

As of 1.0.4, you can call this method multiple times with the same
value of field to allow a single field to be mapped to multiple
prefixes. Multiple terms being generated for such a field, and
combined with  Xapian::Query::OP_OR.

Calling this method with an empty string for field will cause a
Xapian::InvalidArgumentError.

If you call  add_prefix() and  add_boolean_prefix() for the same value
of field, a  Xapian::InvalidOperationError exception will be thrown.

In 1.0.3 and earlier, subsequent calls to this method with the same
value of field had no effect.

Parameters:
-----------

field:  The user visible field name

prefix:  The term prefix to map this to

exclusive:  If true, each document can have at most one value of the
field, so Xapian should combine multiple values with OP_OR. If false,
each document can have multiple values of the field, so Xapian combine
them with OP_AND, as we would with filters with different prefixes.
[default: true] ";

%feature("docstring")  Xapian::QueryParser::add_boolean_prefix "void
Xapian::QueryParser::add_boolean_prefix(const std::string &field,
const std::string &prefix) ";

%feature("docstring")  Xapian::QueryParser::stoplist_begin "

Iterate over terms omitted from the query as stopwords.

TermIterator Xapian::QueryParser::stoplist_begin() const ";

%feature("docstring")  Xapian::QueryParser::stoplist_end "TermIterator Xapian::QueryParser::stoplist_end() const ";

%feature("docstring")  Xapian::QueryParser::unstem_begin "

Iterate over unstemmed forms of the given (stemmed) term used in the
query.

TermIterator Xapian::QueryParser::unstem_begin(const std::string
&term) const ";

%feature("docstring")  Xapian::QueryParser::unstem_end "TermIterator
Xapian::QueryParser::unstem_end(const std::string &) const ";

%feature("docstring")  Xapian::QueryParser::add_valuerangeprocessor "

Register a ValueRangeProcessor.

void
Xapian::QueryParser::add_valuerangeprocessor(Xapian::ValueRangeProcessor
*vrproc) ";

%feature("docstring")  Xapian::QueryParser::get_corrected_query_string
"

Get the spelling-corrected query string.

std::string Xapian::QueryParser::get_corrected_query_string() const

This will only be set if FLAG_SPELLING_CORRECTION is specified when
QueryParser::parse_query() was last called.

If there were no corrections, an empty string is returned. ";

%feature("docstring")  Xapian::QueryParser::get_description "

Return a string describing this object.

std::string Xapian::QueryParser::get_description() const ";


// File: classXapian_1_1QueryParserError.xml
%feature("docstring") Xapian::QueryParserError "

Indicates a query string can't be parsed. ";

%feature("docstring")  Xapian::QueryParserError::QueryParserError "

General purpose constructor which allows setting errno.

Xapian::QueryParserError::QueryParserError(const std::string &msg_,
const std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")  Xapian::QueryParserError::QueryParserError "

Construct from message and errno value.

Xapian::QueryParserError::QueryParserError(const std::string &msg_,
int errno_) ";


// File: classstd_1_1queue.xml
%feature("docstring") std::queue "

STL class. ";


// File: classstd_1_1range__error.xml
%feature("docstring") std::range_error "

STL class. ";


// File: classXapian_1_1RangeError.xml
%feature("docstring") Xapian::RangeError "

RangeError indicates an attempt to access outside the bounds of a
container. ";

%feature("docstring")  Xapian::RangeError::RangeError "

General purpose constructor which allows setting errno.

Xapian::RangeError::RangeError(const std::string &msg_, const
std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")  Xapian::RangeError::RangeError "

Construct from message and errno value.

Xapian::RangeError::RangeError(const std::string &msg_, int errno_) ";


// File: classXapian_1_1Registry.xml
%feature("docstring") Xapian::Registry "

Registry for user subclasses.

This class provides a way for the remote server to look up user
subclasses when unserialising. ";

%feature("docstring")  Xapian::Registry::Registry "

Copy constructor.

Xapian::Registry::Registry(const Registry &other)

The internals are reference counted, so copying is cheap. ";

%feature("docstring")  Xapian::Registry::Registry "

Default constructor.

Xapian::Registry::Registry()

The registry will contain all standard subclasses of user-subclassable
classes. ";

%feature("docstring")  Xapian::Registry::~Registry "Xapian::Registry::~Registry() ";

%feature("docstring")  Xapian::Registry::register_weighting_scheme "

Register a weighting scheme.

void Xapian::Registry::register_weighting_scheme(const Xapian::Weight
&wt) ";

%feature("docstring")  Xapian::Registry::get_weighting_scheme "

Get the weighting scheme given a name.

const Xapian::Weight* Xapian::Registry::get_weighting_scheme(const
std::string &name) const

The returned weighting scheme is owned by the registry object.

Returns NULL if the weighting scheme could not be found. ";

%feature("docstring")  Xapian::Registry::register_posting_source "

Register a user-defined posting source class.

void Xapian::Registry::register_posting_source(const
Xapian::PostingSource &source) ";

%feature("docstring")  Xapian::Registry::get_posting_source "

Get a posting source given a name.

const Xapian::PostingSource*
Xapian::Registry::get_posting_source(const std::string &name) const

The returned posting source is owned by the registry object.

Returns NULL if the posting source could not be found. ";

%feature("docstring")  Xapian::Registry::register_match_spy "

Register a user-defined match spy class.

void Xapian::Registry::register_match_spy(const Xapian::MatchSpy &spy)
";

%feature("docstring")  Xapian::Registry::get_match_spy "

Get a match spy given a name.

const Xapian::MatchSpy* Xapian::Registry::get_match_spy(const
std::string &name) const

The returned match spy is owned by the registry object.

Returns NULL if the match spy could not be found. ";


// File: classstd_1_1list_1_1reverse__iterator.xml
%feature("docstring") std::list::reverse_iterator "

STL iterator class. ";


// File: classstd_1_1map_1_1reverse__iterator.xml
%feature("docstring") std::map::reverse_iterator "

STL iterator class. ";


// File: classstd_1_1vector_1_1reverse__iterator.xml
%feature("docstring") std::vector::reverse_iterator "

STL iterator class. ";


// File: classstd_1_1set_1_1reverse__iterator.xml
%feature("docstring") std::set::reverse_iterator "

STL iterator class. ";


// File: classstd_1_1multiset_1_1reverse__iterator.xml
%feature("docstring") std::multiset::reverse_iterator "

STL iterator class. ";


// File: classstd_1_1basic__string_1_1reverse__iterator.xml
%feature("docstring") std::basic_string::reverse_iterator "

STL iterator class. ";


// File: classstd_1_1multimap_1_1reverse__iterator.xml
%feature("docstring") std::multimap::reverse_iterator "

STL iterator class. ";


// File: classstd_1_1string_1_1reverse__iterator.xml
%feature("docstring") std::string::reverse_iterator "

STL iterator class. ";


// File: classstd_1_1wstring_1_1reverse__iterator.xml
%feature("docstring") std::wstring::reverse_iterator "

STL iterator class. ";


// File: classstd_1_1deque_1_1reverse__iterator.xml
%feature("docstring") std::deque::reverse_iterator "

STL iterator class. ";


// File: classXapian_1_1RSet.xml
%feature("docstring") Xapian::RSet "

A relevance set (R-Set).

This is the set of documents which are marked as relevant, for use in
modifying the term weights, and in performing query expansion. ";

%feature("docstring")  Xapian::RSet::RSet "

Copy constructor.

Xapian::RSet::RSet(const RSet &rset) ";

%feature("docstring")  Xapian::RSet::RSet "

Default constructor.

Xapian::RSet::RSet() ";

%feature("docstring")  Xapian::RSet::~RSet "

Destructor.

Xapian::RSet::~RSet() ";

%feature("docstring")  Xapian::RSet::size "

The number of documents in this R-Set.

Xapian::doccount Xapian::RSet::size() const ";

%feature("docstring")  Xapian::RSet::empty "

Test if this R-Set is empty.

bool Xapian::RSet::empty() const ";

%feature("docstring")  Xapian::RSet::add_document "

Add a document to the relevance set.

void Xapian::RSet::add_document(Xapian::docid did) ";

%feature("docstring")  Xapian::RSet::add_document "

Add a document to the relevance set.

void Xapian::RSet::add_document(const Xapian::MSetIterator &i) ";

%feature("docstring")  Xapian::RSet::remove_document "

Remove a document from the relevance set.

void Xapian::RSet::remove_document(Xapian::docid did) ";

%feature("docstring")  Xapian::RSet::remove_document "

Remove a document from the relevance set.

void Xapian::RSet::remove_document(const Xapian::MSetIterator &i) ";

%feature("docstring")  Xapian::RSet::contains "

Test if a given document in the relevance set.

bool Xapian::RSet::contains(Xapian::docid did) const ";

%feature("docstring")  Xapian::RSet::contains "

Test if a given document in the relevance set.

bool Xapian::RSet::contains(const Xapian::MSetIterator &i) const ";

%feature("docstring")  Xapian::RSet::get_description "

Return a string describing this object.

std::string Xapian::RSet::get_description() const ";


// File: classstd_1_1runtime__error.xml
%feature("docstring") std::runtime_error "

STL class. ";


// File: classXapian_1_1RuntimeError.xml
%feature("docstring") Xapian::RuntimeError "

The base class for exceptions indicating errors only detectable at
runtime.

A subclass of RuntimeError will be thrown if Xapian detects an error
which is exception derived from RuntimeError is thrown when an error
is caused by problems with the data or environment rather than a
programming mistake. ";


// File: classXapian_1_1SerialisationError.xml
%feature("docstring") Xapian::SerialisationError "

Indicates an error in the std::string serialisation of an object. ";

%feature("docstring")  Xapian::SerialisationError::SerialisationError
"

General purpose constructor which allows setting errno.

Xapian::SerialisationError::SerialisationError(const std::string
&msg_, const std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")  Xapian::SerialisationError::SerialisationError
"

Construct from message and errno value.

Xapian::SerialisationError::SerialisationError(const std::string
&msg_, int errno_) ";


// File: classstd_1_1set.xml
%feature("docstring") std::set "

STL class. ";


// File: classXapian_1_1SimpleStopper.xml
%feature("docstring") Xapian::SimpleStopper "

Simple implementation of Stopper class - this will suit most users. ";

%feature("docstring")  Xapian::SimpleStopper::SimpleStopper "

Default constructor.

Xapian::SimpleStopper::SimpleStopper() ";

%feature("docstring")  Xapian::SimpleStopper::SimpleStopper "

Initialise from a pair of iterators.

Xapian::SimpleStopper::SimpleStopper(Iterator begin, Iterator end) ";

%feature("docstring")  Xapian::SimpleStopper::add "

Add a single stop word.

void Xapian::SimpleStopper::add(const std::string &word) ";

%feature("docstring")  Xapian::SimpleStopper::get_description "

Return a string describing this object.

virtual std::string Xapian::SimpleStopper::get_description() const ";


// File: classXapian_1_1Sorter.xml
%feature("docstring") Xapian::Sorter "

Virtual base class for sorter functor. ";


// File: classstd_1_1stack.xml
%feature("docstring") std::stack "

STL class. ";


// File: classXapian_1_1Stem.xml
%feature("docstring") Xapian::Stem "

Class representing a stemming algorithm. ";

%feature("docstring")  Xapian::Stem::Stem "

Copy constructor.

Xapian::Stem::Stem(const Stem &o) ";

%feature("docstring")  Xapian::Stem::Stem "

Construct a Xapian::Stem object which doesn't change terms.

Xapian::Stem::Stem()

Equivalent to Stem(\"none\"). ";

%feature("docstring")  Xapian::Stem::Stem "

Construct a Xapian::Stem object for a particular language.

Xapian::Stem::Stem(const std::string &language)

Parameters:
-----------

language:  Either the English name for the language or the two letter
ISO639 code.

The following language names are understood (aliases follow the name):

none - don't stem terms

danish (da)

dutch (nl)

english (en) - Martin Porter's 2002 revision of his stemmer

english_lovins (lovins) - Lovin's stemmer

english_porter (porter) - Porter's stemmer as described in his 1980
paper

finnish (fi)

french (fr)

german (de)

german2 - Normalises umlauts and

hungarian (hu)

italian (it)

kraaij_pohlmann - A different Dutch stemmer

norwegian (nb, nn, no)

portuguese (pt)

romanian (ro)

russian (ru)

spanish (es)

swedish (sv)

turkish (tr)

Parameters:
-----------

Xapian::InvalidArgumentError:  is thrown if language isn't recognised.
";

%feature("docstring")  Xapian::Stem::Stem "

Construct a Xapian::Stem object with a user-provided stemming
algorithm.

Xapian::Stem::Stem(StemImplementation *p)

You can subclass Xapian::StemImplementation to implement your own
stemming algorithm (or to wrap a third-party algorithm) and then wrap
your implementation in a Xapian::Stem object to pass to the Xapian
API.

The StemImplementation object is reference counted, and so will be
automatically deleted by the Xapian::Stem wrapper when no longer
required. ";

%feature("docstring")  Xapian::Stem::~Stem "

Destructor.

Xapian::Stem::~Stem() ";

%feature("docstring")  Xapian::Stem::get_description "

Return a string describing this object.

std::string Xapian::Stem::get_description() const ";


// File: structXapian_1_1StemImplementation.xml
%feature("docstring") Xapian::StemImplementation "

Class representing a stemming algorithm implementation. ";

%feature("docstring")  Xapian::StemImplementation::~StemImplementation
"

Virtual destructor.

virtual Xapian::StemImplementation::~StemImplementation() ";

%feature("docstring")  Xapian::StemImplementation::get_description "

Return a string describing this object.

virtual std::string Xapian::StemImplementation::get_description()
const =0 ";


// File: classXapian_1_1Stopper.xml
%feature("docstring") Xapian::Stopper "

Base class for stop-word decision functor. ";

%feature("docstring")  Xapian::Stopper::~Stopper "

Class has virtual methods, so provide a virtual destructor.

virtual Xapian::Stopper::~Stopper() ";

%feature("docstring")  Xapian::Stopper::get_description "

Return a string describing this object.

virtual std::string Xapian::Stopper::get_description() const ";


// File: classstd_1_1string.xml
%feature("docstring") std::string "

STL class. ";


// File: classstd_1_1stringstream.xml
%feature("docstring") std::stringstream "

STL class. ";


// File: classXapian_1_1StringValueRangeProcessor.xml
%feature("docstring") Xapian::StringValueRangeProcessor "

Handle a string range.

The end points can be any strings. ";

%feature("docstring")
Xapian::StringValueRangeProcessor::StringValueRangeProcessor "

Constructor.

Xapian::StringValueRangeProcessor::StringValueRangeProcessor(Xapian::valueno
slot_)

Parameters:
-----------

slot_:  The value number to return from operator(). ";

%feature("docstring")
Xapian::StringValueRangeProcessor::StringValueRangeProcessor "

Constructor.

Xapian::StringValueRangeProcessor::StringValueRangeProcessor(Xapian::valueno
slot_, const std::string &str_, bool prefix_=true)

Parameters:
-----------

slot_:  The value number to return from operator().

str_:  A string to look for to recognise values as belonging to this
range.

prefix_:  Flag specifying whether to check for str_ as a prefix or a
suffix. ";


// File: classXapian_1_1TermGenerator.xml
%feature("docstring") Xapian::TermGenerator "

Parses a piece of text and generate terms.

This module takes a piece of text and parses it to produce words which
are then used to generate suitable terms for indexing. The terms
generated are suitable for use with Query objects produced by the
QueryParser class. ";

%feature("docstring")  Xapian::TermGenerator::TermGenerator "

Copy constructor.

Xapian::TermGenerator::TermGenerator(const TermGenerator &o) ";

%feature("docstring")  Xapian::TermGenerator::TermGenerator "

Default constructor.

Xapian::TermGenerator::TermGenerator() ";

%feature("docstring")  Xapian::TermGenerator::~TermGenerator "

Destructor.

Xapian::TermGenerator::~TermGenerator() ";

%feature("docstring")  Xapian::TermGenerator::set_stemmer "

Set the Xapian::Stem object to be used for generating stemmed terms.

void Xapian::TermGenerator::set_stemmer(const Xapian::Stem &stemmer)
";

%feature("docstring")  Xapian::TermGenerator::set_stopper "

Set the Xapian::Stopper object to be used for identifying stopwords.

void Xapian::TermGenerator::set_stopper(const Xapian::Stopper
*stop=NULL)

Stemmed forms of stopwords aren't indexed, but unstemmed forms still
are so that searches for phrases including stop words still work. ";

%feature("docstring")  Xapian::TermGenerator::set_document "

Set the current document.

void Xapian::TermGenerator::set_document(const Xapian::Document &doc)
";

%feature("docstring")  Xapian::TermGenerator::get_document "

Get the current document.

const Xapian::Document& Xapian::TermGenerator::get_document() const ";

%feature("docstring")  Xapian::TermGenerator::set_database "

Set the database to index spelling data to.

void Xapian::TermGenerator::set_database(const
Xapian::WritableDatabase &db) ";

%feature("docstring")  Xapian::TermGenerator::set_flags "

Set flags.

flags Xapian::TermGenerator::set_flags(flags toggle, flags
mask=flags(0))

The new value of flags is: (flags & mask) ^ toggle

To just set the flags, pass the new flags in toggle and the default
value for mask.

Parameters:
-----------

toggle:  Flags to XOR.

mask:  Flags to AND with first.

The old flags setting. ";

%feature("docstring")  Xapian::TermGenerator::index_text "

Index some text.

void Xapian::TermGenerator::index_text(const Xapian::Utf8Iterator
&itor, Xapian::termcount weight=1, const std::string
&prefix=std::string())

Parameters:
-----------

weight:  The wdf increment (default 1).

prefix:  The term prefix to use (default is no prefix). ";

%feature("docstring")  Xapian::TermGenerator::index_text "

Index some text in a std::string.

void Xapian::TermGenerator::index_text(const std::string &text,
Xapian::termcount weight=1, const std::string &prefix=std::string())

Parameters:
-----------

weight:  The wdf increment (default 1).

prefix:  The term prefix to use (default is no prefix). ";

%feature("docstring")
Xapian::TermGenerator::index_text_without_positions "

Index some text without positional information.

void Xapian::TermGenerator::index_text_without_positions(const
Xapian::Utf8Iterator &itor, Xapian::termcount weight=1, const
std::string &prefix=std::string())

Just like index_text, but no positional information is generated. This
means that the database will be significantly smaller, but that phrase
searching and NEAR won't be supported. ";

%feature("docstring")
Xapian::TermGenerator::index_text_without_positions "

Index some text in a std::string without positional information.

void Xapian::TermGenerator::index_text_without_positions(const
std::string &text, Xapian::termcount weight=1, const std::string
&prefix=std::string())

Just like index_text, but no positional information is generated. This
means that the database will be significantly smaller, but that phrase
searching and NEAR won't be supported. ";

%feature("docstring")  Xapian::TermGenerator::increase_termpos "

Increase the termpos used by index_text by delta.

void Xapian::TermGenerator::increase_termpos(Xapian::termcount
delta=100)

This can be used to prevent phrase searches from spanning two
unconnected blocks of text (e.g. the title and body text). ";

%feature("docstring")  Xapian::TermGenerator::get_termpos "

Get the current term position.

Xapian::termcount Xapian::TermGenerator::get_termpos() const ";

%feature("docstring")  Xapian::TermGenerator::set_termpos "

Set the current term position.

void Xapian::TermGenerator::set_termpos(Xapian::termcount termpos) ";

%feature("docstring")  Xapian::TermGenerator::get_description "

Return a string describing this object.

std::string Xapian::TermGenerator::get_description() const ";


// File: classXapian_1_1TermIterator.xml
%feature("docstring") Xapian::TermIterator "

An iterator pointing to items in a list of terms. ";

%feature("docstring")  Xapian::TermIterator::TermIterator "Xapian::TermIterator::TermIterator(Internal *internal_) ";

%feature("docstring")  Xapian::TermIterator::TermIterator "

Default constructor - for declaring an uninitialised iterator.

Xapian::TermIterator::TermIterator() ";

%feature("docstring")  Xapian::TermIterator::~TermIterator "

Destructor.

Xapian::TermIterator::~TermIterator() ";

%feature("docstring")  Xapian::TermIterator::TermIterator "

Copying is allowed.

Xapian::TermIterator::TermIterator(const TermIterator &other)

The internals are reference counted, so copying is also cheap. ";

%feature("docstring")  Xapian::TermIterator::skip_to "

Advance the iterator to the specified term.

void Xapian::TermIterator::skip_to(const std::string &tname)

If the specified term isn't in the list, position ourselves on the
first term after it (or at_end() if no greater terms are present). ";

%feature("docstring")  Xapian::TermIterator::get_wdf "

Return the wdf of the current term (if meaningful).

Xapian::termcount Xapian::TermIterator::get_wdf() const

The wdf (within document frequency) is the number of occurrences of a
term in a particular document. ";

%feature("docstring")  Xapian::TermIterator::get_termfreq "

Return the term frequency of the current term (if meaningful).

Xapian::doccount Xapian::TermIterator::get_termfreq() const

The term frequency is the number of documents which a term indexes. ";

%feature("docstring")  Xapian::TermIterator::positionlist_count "

Return length of positionlist for current term.

Xapian::termcount Xapian::TermIterator::positionlist_count() const ";

%feature("docstring")  Xapian::TermIterator::positionlist_begin "

Return PositionIterator pointing to start of positionlist for current
term.

PositionIterator Xapian::TermIterator::positionlist_begin() const ";

%feature("docstring")  Xapian::TermIterator::positionlist_end "

Return PositionIterator pointing to end of positionlist for current
term.

PositionIterator Xapian::TermIterator::positionlist_end() const ";

%feature("docstring")  Xapian::TermIterator::get_description "

Return a string describing this object.

std::string Xapian::TermIterator::get_description() const ";


// File: classXapian_1_1TradWeight.xml
%feature("docstring") Xapian::TradWeight "

Xapian::Weight subclass implementing the traditional probabilistic
formula.

This class implements the \"traditional\" Probabilistic Weighting
scheme, as described by the early papers on Probabilistic Retrieval.
BM25 generally gives better results.

TradWeight(k) is equivalent to BM25Weight(k, 0, 0, 1, 0), except that
the latter returns weights (k+1) times larger. ";

%feature("docstring")  Xapian::TradWeight::TradWeight "

Construct a TradWeight.

Xapian::TradWeight::TradWeight(double k=1.0)

Parameters:
-----------

k:  A non-negative parameter controlling how influential within-
document- frequency (wdf) and document length are. k=0 means that wdf
and document length don't affect the weights. The larger k1 is, the
more they do. (default 1) ";

%feature("docstring")  Xapian::TradWeight::name "

Return the name of this weighting scheme.

std::string Xapian::TradWeight::name() const

This name is used by the remote backend. It is passed along with the
serialised parameters to the remote server so that it knows which
class to create.

Return the full namespace-qualified name of your class here - if your
class is called FooWeight, return \"FooWeight\" from this method (
Xapian::BM25Weight returns \"Xapian::BM25Weight\" here).

If you don't want to support the remote backend, you can use the
default implementation which simply returns an empty string. ";

%feature("docstring")  Xapian::TradWeight::serialise "

Return this object's parameters serialised as a single string.

std::string Xapian::TradWeight::serialise() const

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.
";

%feature("docstring")  Xapian::TradWeight::unserialise "

Unserialise parameters.

TradWeight* Xapian::TradWeight::unserialise(const std::string &s)
const

This method unserialises parameters serialised by the  serialise()
method and allocates and returns a new object initialised with them.

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".
";

%feature("docstring")  Xapian::TradWeight::get_sumpart "

Calculate the weight contribution for this object's term to a
document.

Xapian::weight Xapian::TradWeight::get_sumpart(Xapian::termcount wdf,
Xapian::termcount doclen) const

The parameters give information about the document which may be used
in the calculations:

Parameters:
-----------

wdf:  The within document frequency of the term in the document.

doclen:  The document's length (unnormalised). ";

%feature("docstring")  Xapian::TradWeight::get_maxpart "

Return an upper bound on what get_sumpart() can return for any
document.

Xapian::weight Xapian::TradWeight::get_maxpart() const

This information is used by the matcher to perform various
optimisations, so strive to make the bound as tight as possible. ";

%feature("docstring")  Xapian::TradWeight::get_sumextra "

Calculate the term-independent weight component for a document.

Xapian::weight Xapian::TradWeight::get_sumextra(Xapian::termcount
doclen) const

The parameter gives information about the document which may be used
in the calculations:

Parameters:
-----------

doclen:  The document's length (unnormalised). ";

%feature("docstring")  Xapian::TradWeight::get_maxextra "

Return an upper bound on what get_sumextra() can return for any
document.

Xapian::weight Xapian::TradWeight::get_maxextra() const

This information is used by the matcher to perform various
optimisations, so strive to make the bound as tight as possible. ";


// File: classstd_1_1underflow__error.xml
%feature("docstring") std::underflow_error "

STL class. ";


// File: classXapian_1_1UnimplementedError.xml
%feature("docstring") Xapian::UnimplementedError "

UnimplementedError indicates an attempt to use an unimplemented
feature. ";

%feature("docstring")  Xapian::UnimplementedError::UnimplementedError
"

General purpose constructor which allows setting errno.

Xapian::UnimplementedError::UnimplementedError(const std::string
&msg_, const std::string &context_=std::string(), int errno_=0) ";

%feature("docstring")  Xapian::UnimplementedError::UnimplementedError
"

Construct from message and errno value.

Xapian::UnimplementedError::UnimplementedError(const std::string
&msg_, int errno_) ";


// File: classXapian_1_1Utf8Iterator.xml
%feature("docstring") Xapian::Utf8Iterator "

An iterator which returns Unicode character values from a UTF-8
encoded string. ";

%feature("docstring")  Xapian::Utf8Iterator::raw "

Return the raw const char * pointer for the current position.

const char* Xapian::Utf8Iterator::raw() const ";

%feature("docstring")  Xapian::Utf8Iterator::left "

Return the number of bytes left in the iterator's buffer.

size_t Xapian::Utf8Iterator::left() const ";

%feature("docstring")  Xapian::Utf8Iterator::assign "

Assign a new string to the iterator.

void Xapian::Utf8Iterator::assign(const char *p_, size_t len)

The iterator will forget the string it was iterating through, and
return characters from the start of the new string when next called.
The string is not copied into the iterator, so it must remain valid
while the iteration is in progress.

Parameters:
-----------

p_:  A pointer to the start of the string to read.

len:  The length of the string to read. ";

%feature("docstring")  Xapian::Utf8Iterator::assign "

Assign a new string to the iterator.

void Xapian::Utf8Iterator::assign(const std::string &s)

The iterator will forget the string it was iterating through, and
return characters from the start of the new string when next called.
The string is not copied into the iterator, so it must remain valid
while the iteration is in progress.

Parameters:
-----------

s:  The string to read. Must not be modified while the iteration is in
progress. ";

%feature("docstring")  Xapian::Utf8Iterator::Utf8Iterator "

Create an iterator given a pointer to a null terminated string.

Xapian::Utf8Iterator::Utf8Iterator(const char *p_)

The iterator will return characters from the start of the string when
next called. The string is not copied into the iterator, so it must
remain valid while the iteration is in progress.

Parameters:
-----------

p_:  A pointer to the start of the null terminated string to read. ";

%feature("docstring")  Xapian::Utf8Iterator::Utf8Iterator "

Create an iterator given a pointer and a length.

Xapian::Utf8Iterator::Utf8Iterator(const char *p_, size_t len)

The iterator will return characters from the start of the string when
next called. The string is not copied into the iterator, so it must
remain valid while the iteration is in progress.

Parameters:
-----------

p_:  A pointer to the start of the string to read.

len:  The length of the string to read. ";

%feature("docstring")  Xapian::Utf8Iterator::Utf8Iterator "

Create an iterator given a string.

Xapian::Utf8Iterator::Utf8Iterator(const std::string &s)

The iterator will return characters from the start of the string when
next called. The string is not copied into the iterator, so it must
remain valid while the iteration is in progress.

Parameters:
-----------

s:  The string to read. Must not be modified while the iteration is in
progress. ";

%feature("docstring")  Xapian::Utf8Iterator::Utf8Iterator "

Create an iterator which is at the end of its iteration.

Xapian::Utf8Iterator::Utf8Iterator()

This can be compared to another iterator to check if the other
iterator has reached its end. ";


// File: classstd_1_1valarray.xml
%feature("docstring") std::valarray "

STL class. ";


// File: classXapian_1_1ValueCountMatchSpy.xml
%feature("docstring") Xapian::ValueCountMatchSpy "

Class for counting the frequencies of values in the matching
documents. ";

%feature("docstring")  Xapian::ValueCountMatchSpy::ValueCountMatchSpy
"

Construct an empty ValueCountMatchSpy.

Xapian::ValueCountMatchSpy::ValueCountMatchSpy() ";

%feature("docstring")  Xapian::ValueCountMatchSpy::ValueCountMatchSpy
"

Construct a MatchSpy which counts the values in a particular slot.

Xapian::ValueCountMatchSpy::ValueCountMatchSpy(Xapian::valueno slot_)
";

%feature("docstring")  Xapian::ValueCountMatchSpy::get_total "

Return the total number of documents tallied.

size_t Xapian::ValueCountMatchSpy::get_total() const ";

%feature("docstring")  Xapian::ValueCountMatchSpy::values_begin "

Get an iterator over the values seen in the slot.

TermIterator Xapian::ValueCountMatchSpy::values_begin() const

Items will be returned in ascending alphabetical order.

During the iteration, the frequency of the current value can be
obtained with the get_termfreq() method on the iterator. ";

%feature("docstring")  Xapian::ValueCountMatchSpy::values_end "

End iterator corresponding to values_begin().

TermIterator Xapian::ValueCountMatchSpy::values_end() const ";

%feature("docstring")  Xapian::ValueCountMatchSpy::top_values_begin "

Get an iterator over the most frequent values seen in the slot.

TermIterator Xapian::ValueCountMatchSpy::top_values_begin(size_t
maxvalues) const

Items will be returned in descending order of frequency. Values with
the same frequency will be returned in ascending alphabetical order.

During the iteration, the frequency of the current value can be
obtained with the get_termfreq() method on the iterator.

Parameters:
-----------

maxvalues:  The maximum number of values to return. ";

%feature("docstring")  Xapian::ValueCountMatchSpy::top_values_end "

End iterator corresponding to top_values_begin().

TermIterator Xapian::ValueCountMatchSpy::top_values_end(size_t) const
";

%feature("docstring")  Xapian::ValueCountMatchSpy::clone "

Clone the match spy.

virtual MatchSpy* Xapian::ValueCountMatchSpy::clone() const

The clone should inherit the configuration of the parent, but need not
inherit the state. ie, the clone does not need to be passed
information about the results seen by the parent.

If you don't want to support the remote backend in your match spy, you
can use the default implementation which simply throws
Xapian::UnimplementedError.

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".
";

%feature("docstring")  Xapian::ValueCountMatchSpy::name "

Return the name of this match spy.

virtual std::string Xapian::ValueCountMatchSpy::name() const

This name is used by the remote backend. It is passed with the
serialised parameters to the remote server so that it knows which
class to create.

Return the full namespace-qualified name of your class here - if your
class is called MyApp::FooMatchSpy, return \"MyApp::FooMatchSpy\" from
this method.

If you don't want to support the remote backend in your match spy, you
can use the default implementation which simply throws
Xapian::UnimplementedError. ";

%feature("docstring")  Xapian::ValueCountMatchSpy::serialise "

Return this object's parameters serialised as a single string.

virtual std::string Xapian::ValueCountMatchSpy::serialise() const

If you don't want to support the remote backend in your match spy, you
can use the default implementation which simply throws
Xapian::UnimplementedError. ";

%feature("docstring")  Xapian::ValueCountMatchSpy::unserialise "

Unserialise parameters.

virtual MatchSpy* Xapian::ValueCountMatchSpy::unserialise(const
std::string &s, const Registry &context) const

This method unserialises parameters serialised by the  serialise()
method and allocates and returns a new object initialised with them.

If you don't want to support the remote backend in your match spy, you
can use the default implementation which simply throws
Xapian::UnimplementedError.

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".
";

%feature("docstring")  Xapian::ValueCountMatchSpy::serialise_results "

Serialise the results of this match spy.

virtual std::string Xapian::ValueCountMatchSpy::serialise_results()
const

If you don't want to support the remote backend in your match spy, you
can use the default implementation which simply throws
Xapian::UnimplementedError. ";

%feature("docstring")  Xapian::ValueCountMatchSpy::merge_results "

Unserialise some results, and merge them into this matchspy.

virtual void Xapian::ValueCountMatchSpy::merge_results(const
std::string &s)

The order in which results are merged should not be significant, since
this order is not specified (and will vary depending on the speed of
the search in each sub-database).

If you don't want to support the remote backend in your match spy, you
can use the default implementation which simply throws
Xapian::UnimplementedError. ";

%feature("docstring")  Xapian::ValueCountMatchSpy::get_description "

Return a string describing this object.

virtual std::string Xapian::ValueCountMatchSpy::get_description()
const

This default implementation returns a generic answer, to avoid forcing
those deriving their own MatchSpy subclasses from having to implement
this (they may not care what get_description() gives for their
subclass). ";


// File: classXapian_1_1ValueIterator.xml
%feature("docstring") Xapian::ValueIterator "

Class for iterating over document values. ";

%feature("docstring")  Xapian::ValueIterator::ValueIterator "

Copy constructor.

Xapian::ValueIterator::ValueIterator(const ValueIterator &o) ";

%feature("docstring")  Xapian::ValueIterator::ValueIterator "Xapian::ValueIterator::ValueIterator(const ValueIteratorEnd_ &) ";

%feature("docstring")  Xapian::ValueIterator::ValueIterator "

Default constructor.

Xapian::ValueIterator::ValueIterator()

Creates an uninitialised iterator, which can't be used before being
assigned to, but is sometimes syntactically convenient. ";

%feature("docstring")  Xapian::ValueIterator::~ValueIterator "

Destructor.

Xapian::ValueIterator::~ValueIterator() ";

%feature("docstring")  Xapian::ValueIterator::get_docid "

Return the docid at the current position.

Xapian::docid Xapian::ValueIterator::get_docid() const

If we're iterating over values of a document, this method will throw
Xapian::InvalidOperationError. ";

%feature("docstring")  Xapian::ValueIterator::get_valueno "

Return the value slot number for the current position.

Xapian::valueno Xapian::ValueIterator::get_valueno() const

If the iterator is over all values in a slot, this returns that slot's
number. If the iterator is over the values in a particular document,
it returns the number of each slot in turn. ";

%feature("docstring")  Xapian::ValueIterator::skip_to "

Advance the iterator to document id or value slot docid_or_slot.

void Xapian::ValueIterator::skip_to(Xapian::docid docid_or_slot)

If this iterator is over values in a document, then this method
advances the iterator to value slot docid_or_slot, or the first slot
after it if there is no value in slot slot.

If this iterator is over values in a particular slot, then this method
advances the iterator to document id docid_or_slot, or the first
document id after it if there is no value in the slot we're iterating
over for document docid_or_slot.

Note: The \"two-faced\" nature of this method is due to how C++
overloading works. Xapian::docid and Xapian::valueno are both typedefs
for the same unsigned integer type, so overloading can't distinguish
them. ";

%feature("docstring")  Xapian::ValueIterator::check "

Check if the specified docid occurs.

bool Xapian::ValueIterator::check(Xapian::docid docid)

The caller is required to ensure that the specified document id did
actually exists in the database.

This method acts like skip_to() if that can be done at little extra
cost, in which case it then returns true. This is how brass and chert
databases behave because they store values in streams which allow for
an efficient implementation of skip_to().

Otherwise it simply checks if a particular docid is present. If it is,
it returns true. If it isn't, it returns false, and leaves the
position unspecified (and hence the result of calling methods which
depends on the current position, such as get_docid(), are also
unspecified). In this state, next() will advance to the first matching
position after document did, and skip_to() will act as it would if the
position was the first matching position after document did.

Currently the inmemory, flint, and remote backends behave in the
latter way because they don't support streamed values and so skip_to()
must check each document it skips over which is significantly slower.
";

%feature("docstring")  Xapian::ValueIterator::get_description "

Return a string describing this object.

std::string Xapian::ValueIterator::get_description() const ";


// File: classXapian_1_1ValueIteratorEnd__.xml


// File: classXapian_1_1ValueMapPostingSource.xml
%feature("docstring") Xapian::ValueMapPostingSource "

A posting source which looks up weights in a map using values as the
key.

This allows will return entries for all documents in the given
database which have a value in the slot specified. The values will be
mapped to the corresponding weight in the weight map. If there is no
mapping for a particular value, the default weight will be returned
(which itself defaults to 0.0). ";

%feature("docstring")
Xapian::ValueMapPostingSource::ValueMapPostingSource "

Construct a ValueWeightPostingSource.

Xapian::ValueMapPostingSource::ValueMapPostingSource(Xapian::valueno
slot_)

Parameters:
-----------

slot_:  The value slot to read values from. ";

%feature("docstring")  Xapian::ValueMapPostingSource::add_mapping "

Add a mapping.

void Xapian::ValueMapPostingSource::add_mapping(const std::string
&key, double weight)

Parameters:
-----------

key:  The key looked up from the value slot.

weight:  The weight to give this key. ";

%feature("docstring")  Xapian::ValueMapPostingSource::clear_mappings "

Clear all mappings.

void Xapian::ValueMapPostingSource::clear_mappings() ";

%feature("docstring")
Xapian::ValueMapPostingSource::set_default_weight "

Set a default weight for document values not in the map.

void Xapian::ValueMapPostingSource::set_default_weight(double wt) ";

%feature("docstring")  Xapian::ValueMapPostingSource::get_weight "

Return the weight contribution for the current document.

Xapian::weight Xapian::ValueMapPostingSource::get_weight() const

This default implementation always returns 0, for convenience when
implementing \"weight-less\" PostingSource subclasses.

This method may assume that it will only be called when there is a
\"current document\". In detail: Xapian will always call init() on a
PostingSource before calling this for the first time. It will also
only call this if the PostingSource reports that it is pointing to a
valid document (ie, it will not call it before calling at least one of
next(), skip_to() or check(), and will ensure that the PostingSource
is not at the end by calling at_end()). ";

%feature("docstring")  Xapian::ValueMapPostingSource::clone "

Clone the posting source.

ValueMapPostingSource* Xapian::ValueMapPostingSource::clone() const

The clone should inherit the configuration of the parent, but need not
inherit the state. ie, the clone does not need to be in the same
iteration position as the original: the matcher will always call
init() on the clone before attempting to move the iterator, or read
the information about the current position of the iterator.

This may return NULL to indicate that cloning is not supported. In
this case, the PostingSource may only be used with a single-database
search.

The default implementation returns NULL.

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".
";

%feature("docstring")  Xapian::ValueMapPostingSource::name "

Name of the posting source class.

std::string Xapian::ValueMapPostingSource::name() const

This is used when serialising and unserialising posting sources; for
example, for performing remote searches.

If the subclass is in a C++ namespace, the namespace should be
included in the name, using \"::\" as a separator. For example, for a
PostingSource subclass called \"FooPostingSource\" in the \"Xapian\"
namespace the result of this call should be
\"Xapian::FooPostingSource\".

This should only be implemented if serialise() and unserialise() are
also implemented. The default implementation returns an empty string.

If this returns an empty string, Xapian will assume that serialise()
and unserialise() are not implemented. ";

%feature("docstring")  Xapian::ValueMapPostingSource::serialise "

Serialise object parameters into a string.

std::string Xapian::ValueMapPostingSource::serialise() const

The serialised parameters should represent the configuration of the
posting source, but need not (indeed, should not) represent the
current iteration state.

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.
";

%feature("docstring")  Xapian::ValueMapPostingSource::unserialise "

Create object given string serialisation returned by serialise().

ValueMapPostingSource*
Xapian::ValueMapPostingSource::unserialise(const std::string &s) const

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.

Parameters:
-----------

s:  A serialised instance of this PostingSource subclass. ";

%feature("docstring")  Xapian::ValueMapPostingSource::init "

Set this PostingSource to the start of the list of postings.

void Xapian::ValueMapPostingSource::init(const Database &db_)

This is called automatically by the matcher prior to each query being
processed.

If a PostingSource is used for multiple searches,  init() will
therefore be called multiple times, and must handle this by using the
database passed in the most recent call.

Parameters:
-----------

db:  The database which the PostingSource should iterate through.

Note: the database supplied to this method must not be modified: in
particular, the reopen() method should not be called on it.

Note: in the case of a multi-database search, a separate PostingSource
will be used for each database (the separate PostingSources will be
obtained using  clone()), and each PostingSource will be passed one of
the sub-databases as the db parameter here. The db parameter will
therefore always refer to a single database. All docids passed to, or
returned from, the PostingSource refer to docids in that single
database, rather than in the multi- database. ";

%feature("docstring")  Xapian::ValueMapPostingSource::get_description
"

Return a string describing this object.

std::string Xapian::ValueMapPostingSource::get_description() const

This default implementation returns a generic answer. This default it
provided to avoid forcing those deriving their own PostingSource
subclass from having to implement this (they may not care what
get_description() gives for their subclass). ";


// File: classXapian_1_1ValuePostingSource.xml
%feature("docstring") Xapian::ValuePostingSource "

A posting source which generates weights from a value slot.

This is a base class for classes which generate weights using values
stored in the specified slot. For example, ValueWeightPostingSource
uses sortable_unserialise to convert values directly to weights.

The upper bound on the weight returned is set to DBL_MAX. Subclasses
should call set_maxweight() in their init() methods after calling
ValuePostingSource::init() if they know a tighter bound on the weight.
";

%feature("docstring")  Xapian::ValuePostingSource::ValuePostingSource
"

Construct a ValuePostingSource.

Xapian::ValuePostingSource::ValuePostingSource(Xapian::valueno slot_)

Parameters:
-----------

slot_:  The value slot to read values from. ";

%feature("docstring")  Xapian::ValuePostingSource::get_termfreq_min "

A lower bound on the number of documents this object can return.

Xapian::doccount Xapian::ValuePostingSource::get_termfreq_min() const

Xapian will always call init() on a PostingSource before calling this
for the first time. ";

%feature("docstring")  Xapian::ValuePostingSource::get_termfreq_est "

An estimate of the number of documents this object can return.

Xapian::doccount Xapian::ValuePostingSource::get_termfreq_est() const

It must always be true that:

get_termfreq_min() <= get_termfreq_est() <= get_termfreq_max()

Xapian will always call init() on a PostingSource before calling this
for the first time. ";

%feature("docstring")  Xapian::ValuePostingSource::get_termfreq_max "

An upper bound on the number of documents this object can return.

Xapian::doccount Xapian::ValuePostingSource::get_termfreq_max() const

Xapian will always call init() on a PostingSource before calling this
for the first time. ";

%feature("docstring")  Xapian::ValuePostingSource::next "

Advance the current position to the next matching document.

void Xapian::ValuePostingSource::next(Xapian::weight min_wt)

The PostingSource starts before the first entry in the list, so next()
must be called before any methods which need the context of the
current position.

Xapian will always call init() on a PostingSource before calling this
for the first time.

Parameters:
-----------

min_wt:  The minimum weight contribution that is needed (this is just
a hint which subclasses may ignore). ";

%feature("docstring")  Xapian::ValuePostingSource::skip_to "

Advance to the specified docid.

void Xapian::ValuePostingSource::skip_to(Xapian::docid min_docid,
Xapian::weight min_wt)

If the specified docid isn't in the list, position ourselves on the
first document after it (or at_end() if no greater docids are
present).

If the current position is already the specified docid, this method
will leave the position unmodified.

If the specified docid is earlier than the current position, the
behaviour is unspecified. A sensible behaviour would be to leave the
current position unmodified, but it is also reasonable to move to the
specified docid.

The default implementation calls next() repeatedly, which works but
skip_to() can often be implemented much more efficiently.

Xapian will always call init() on a PostingSource before calling this
for the first time.

Note: in the case of a multi-database search, the docid specified is
the docid in the single subdatabase relevant to this posting source.
See the  init() method for details.

Parameters:
-----------

min_wt:  The minimum weight contribution that is needed (this is just
a hint which subclasses may ignore). ";

%feature("docstring")  Xapian::ValuePostingSource::check "

Check if the specified docid occurs.

bool Xapian::ValuePostingSource::check(Xapian::docid min_docid,
Xapian::weight min_wt)

The caller is required to ensure that the specified document id did
actually exists in the database. If it does, it must move to that
document id, and return true. If it does not, it may either:

return true, having moved to a definite position (including
\"at_end\"), which must be the same position as skip_to() would have
moved to.

or

return false, having moved to an \"indeterminate\" position, such that
a subsequent call to next() or skip_to() will move to the next
matching position after did.

Generally, this method should act like skip_to() and return true if
that can be done at little extra cost.

Otherwise it should simply check if a particular docid is present,
returning true if it is, and false if it isn't.

The default implementation calls skip_to() and always returns true.

Xapian will always call init() on a PostingSource before calling this
for the first time.

Note: in the case of a multi-database search, the docid specified is
the docid in the single subdatabase relevant to this posting source.
See the  init() method for details. ";

%feature("docstring")  Xapian::ValuePostingSource::at_end "

Return true if the current position is past the last entry in this
list.

bool Xapian::ValuePostingSource::at_end() const

At least one of  next(),  skip_to() or  check() will be called before
this method is first called. ";

%feature("docstring")  Xapian::ValuePostingSource::get_docid "

Return the current docid.

Xapian::docid Xapian::ValuePostingSource::get_docid() const

This method may assume that it will only be called when there is a
\"current document\". See  get_weight() for details.

Note: in the case of a multi-database search, the returned docid
should be in the single subdatabase relevant to this posting source.
See the  init() method for details. ";

%feature("docstring")  Xapian::ValuePostingSource::init "

Set this PostingSource to the start of the list of postings.

void Xapian::ValuePostingSource::init(const Database &db_)

This is called automatically by the matcher prior to each query being
processed.

If a PostingSource is used for multiple searches,  init() will
therefore be called multiple times, and must handle this by using the
database passed in the most recent call.

Parameters:
-----------

db:  The database which the PostingSource should iterate through.

Note: the database supplied to this method must not be modified: in
particular, the reopen() method should not be called on it.

Note: in the case of a multi-database search, a separate PostingSource
will be used for each database (the separate PostingSources will be
obtained using  clone()), and each PostingSource will be passed one of
the sub-databases as the db parameter here. The db parameter will
therefore always refer to a single database. All docids passed to, or
returned from, the PostingSource refer to docids in that single
database, rather than in the multi- database. ";


// File: structXapian_1_1ValueRangeProcessor.xml
%feature("docstring") Xapian::ValueRangeProcessor "

Base class for value range processors. ";

%feature("docstring")
Xapian::ValueRangeProcessor::~ValueRangeProcessor "

Destructor.

virtual Xapian::ValueRangeProcessor::~ValueRangeProcessor() ";


// File: classXapian_1_1ValueSetMatchDecider.xml
%feature("docstring") Xapian::ValueSetMatchDecider "

MatchDecider filtering results based on whether document values are in
a user- defined set. ";

%feature("docstring")
Xapian::ValueSetMatchDecider::ValueSetMatchDecider "

Construct a ValueSetMatchDecider.

Xapian::ValueSetMatchDecider::ValueSetMatchDecider(Xapian::valueno
slot, bool inclusive_)

Parameters:
-----------

slot:  The value slot number to look in.

inclusive_:  If true, match decider accepts documents which have a
value in the specified slot which is a member of the test set; if
false, match decider accepts documents which do not have a value in
the specified slot. ";

%feature("docstring")  Xapian::ValueSetMatchDecider::add_value "

Add a value to the test set.

void Xapian::ValueSetMatchDecider::add_value(const std::string &value)

Parameters:
-----------

value:  The value to add to the test set. ";

%feature("docstring")  Xapian::ValueSetMatchDecider::remove_value "

Remove a value from the test set.

void Xapian::ValueSetMatchDecider::remove_value(const std::string
&value)

Parameters:
-----------

value:  The value to remove from the test set. ";


// File: classXapian_1_1ValueWeightPostingSource.xml
%feature("docstring") Xapian::ValueWeightPostingSource "

A posting source which reads weights from a value slot.

This returns entries for all documents in the given database which
have a non empty values in the specified slot. It returns a weight
calculated by applying sortable_unserialise to the value stored in the
slot (so the values stored should probably have been calculated by
applying sortable_serialise to a floating point number at index time).

The upper bound on the weight returned is set using the upper bound on
the values in the specified slot, or DBL_MAX if value bounds aren't
supported by the current backend.

For efficiency, this posting source doesn't check that the stored
values are valid in any way, so it will never raise an exception due
to invalid stored values. In particular, it doesn't ensure that the
unserialised values are positive, which is a requirement for weights.
The behaviour if the slot contains values which unserialise to
negative values is undefined. ";

%feature("docstring")
Xapian::ValueWeightPostingSource::ValueWeightPostingSource "

Construct a ValueWeightPostingSource.

Xapian::ValueWeightPostingSource::ValueWeightPostingSource(Xapian::valueno
slot_)

Parameters:
-----------

slot_:  The value slot to read values from. ";

%feature("docstring")  Xapian::ValueWeightPostingSource::get_weight "

Return the weight contribution for the current document.

Xapian::weight Xapian::ValueWeightPostingSource::get_weight() const

This default implementation always returns 0, for convenience when
implementing \"weight-less\" PostingSource subclasses.

This method may assume that it will only be called when there is a
\"current document\". In detail: Xapian will always call init() on a
PostingSource before calling this for the first time. It will also
only call this if the PostingSource reports that it is pointing to a
valid document (ie, it will not call it before calling at least one of
next(), skip_to() or check(), and will ensure that the PostingSource
is not at the end by calling at_end()). ";

%feature("docstring")  Xapian::ValueWeightPostingSource::clone "

Clone the posting source.

ValueWeightPostingSource* Xapian::ValueWeightPostingSource::clone()
const

The clone should inherit the configuration of the parent, but need not
inherit the state. ie, the clone does not need to be in the same
iteration position as the original: the matcher will always call
init() on the clone before attempting to move the iterator, or read
the information about the current position of the iterator.

This may return NULL to indicate that cloning is not supported. In
this case, the PostingSource may only be used with a single-database
search.

The default implementation returns NULL.

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".
";

%feature("docstring")  Xapian::ValueWeightPostingSource::name "

Name of the posting source class.

std::string Xapian::ValueWeightPostingSource::name() const

This is used when serialising and unserialising posting sources; for
example, for performing remote searches.

If the subclass is in a C++ namespace, the namespace should be
included in the name, using \"::\" as a separator. For example, for a
PostingSource subclass called \"FooPostingSource\" in the \"Xapian\"
namespace the result of this call should be
\"Xapian::FooPostingSource\".

This should only be implemented if serialise() and unserialise() are
also implemented. The default implementation returns an empty string.

If this returns an empty string, Xapian will assume that serialise()
and unserialise() are not implemented. ";

%feature("docstring")  Xapian::ValueWeightPostingSource::serialise "

Serialise object parameters into a string.

std::string Xapian::ValueWeightPostingSource::serialise() const

The serialised parameters should represent the configuration of the
posting source, but need not (indeed, should not) represent the
current iteration state.

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.
";

%feature("docstring")  Xapian::ValueWeightPostingSource::unserialise "

Create object given string serialisation returned by serialise().

ValueWeightPostingSource*
Xapian::ValueWeightPostingSource::unserialise(const std::string &s)
const

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.

Parameters:
-----------

s:  A serialised instance of this PostingSource subclass. ";

%feature("docstring")  Xapian::ValueWeightPostingSource::init "

Set this PostingSource to the start of the list of postings.

void Xapian::ValueWeightPostingSource::init(const Database &db_)

This is called automatically by the matcher prior to each query being
processed.

If a PostingSource is used for multiple searches,  init() will
therefore be called multiple times, and must handle this by using the
database passed in the most recent call.

Parameters:
-----------

db:  The database which the PostingSource should iterate through.

Note: the database supplied to this method must not be modified: in
particular, the reopen() method should not be called on it.

Note: in the case of a multi-database search, a separate PostingSource
will be used for each database (the separate PostingSources will be
obtained using  clone()), and each PostingSource will be passed one of
the sub-databases as the db parameter here. The db parameter will
therefore always refer to a single database. All docids passed to, or
returned from, the PostingSource refer to docids in that single
database, rather than in the multi- database. ";

%feature("docstring")
Xapian::ValueWeightPostingSource::get_description "

Return a string describing this object.

std::string Xapian::ValueWeightPostingSource::get_description() const

This default implementation returns a generic answer. This default it
provided to avoid forcing those deriving their own PostingSource
subclass from having to implement this (they may not care what
get_description() gives for their subclass). ";


// File: classstd_1_1vector.xml
%feature("docstring") std::vector "

STL class. ";


// File: classXapian_1_1Weight.xml
%feature("docstring") Xapian::Weight "

Abstract base class for weighting schemes. ";

%feature("docstring")  Xapian::Weight::~Weight "

Virtual destructor, because we have virtual methods.

virtual Xapian::Weight::~Weight() ";

%feature("docstring")  Xapian::Weight::clone "

Clone this object.

virtual Weight* Xapian::Weight::clone() const =0

This method allocates and returns a copy of the object it is called
on.

If your subclass is called FooWeight and has parameters a and b, then
you would implement FooWeight::clone() like so:

FooWeight * FooWeight::clone() const { return new FooWeight(a, b); }

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".
";

%feature("docstring")  Xapian::Weight::name "

Return the name of this weighting scheme.

virtual std::string Xapian::Weight::name() const

This name is used by the remote backend. It is passed along with the
serialised parameters to the remote server so that it knows which
class to create.

Return the full namespace-qualified name of your class here - if your
class is called FooWeight, return \"FooWeight\" from this method (
Xapian::BM25Weight returns \"Xapian::BM25Weight\" here).

If you don't want to support the remote backend, you can use the
default implementation which simply returns an empty string. ";

%feature("docstring")  Xapian::Weight::serialise "

Return this object's parameters serialised as a single string.

virtual std::string Xapian::Weight::serialise() const

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.
";

%feature("docstring")  Xapian::Weight::unserialise "

Unserialise parameters.

virtual Weight* Xapian::Weight::unserialise(const std::string &s)
const

This method unserialises parameters serialised by the  serialise()
method and allocates and returns a new object initialised with them.

If you don't want to support the remote backend, you can use the
default implementation which simply throws Xapian::UnimplementedError.

Note that the returned object will be deallocated by Xapian after use
with \"delete\". It must therefore have been allocated with \"new\".
";

%feature("docstring")  Xapian::Weight::get_sumpart "

Calculate the weight contribution for this object's term to a
document.

virtual Xapian::weight Xapian::Weight::get_sumpart(Xapian::termcount
wdf, Xapian::termcount doclen) const =0

The parameters give information about the document which may be used
in the calculations:

Parameters:
-----------

wdf:  The within document frequency of the term in the document.

doclen:  The document's length (unnormalised). ";

%feature("docstring")  Xapian::Weight::get_maxpart "

Return an upper bound on what get_sumpart() can return for any
document.

virtual Xapian::weight Xapian::Weight::get_maxpart() const =0

This information is used by the matcher to perform various
optimisations, so strive to make the bound as tight as possible. ";

%feature("docstring")  Xapian::Weight::get_sumextra "

Calculate the term-independent weight component for a document.

virtual Xapian::weight Xapian::Weight::get_sumextra(Xapian::termcount
doclen) const =0

The parameter gives information about the document which may be used
in the calculations:

Parameters:
-----------

doclen:  The document's length (unnormalised). ";

%feature("docstring")  Xapian::Weight::get_maxextra "

Return an upper bound on what get_sumextra() can return for any
document.

virtual Xapian::weight Xapian::Weight::get_maxextra() const =0

This information is used by the matcher to perform various
optimisations, so strive to make the bound as tight as possible. ";


// File: classstd_1_1wfstream.xml
%feature("docstring") std::wfstream "

STL class. ";


// File: classstd_1_1wifstream.xml
%feature("docstring") std::wifstream "

STL class. ";


// File: classstd_1_1wios.xml
%feature("docstring") std::wios "

STL class. ";


// File: classstd_1_1wistream.xml
%feature("docstring") std::wistream "

STL class. ";


// File: classstd_1_1wistringstream.xml
%feature("docstring") std::wistringstream "

STL class. ";


// File: classstd_1_1wofstream.xml
%feature("docstring") std::wofstream "

STL class. ";


// File: classstd_1_1wostream.xml
%feature("docstring") std::wostream "

STL class. ";


// File: classstd_1_1wostringstream.xml
%feature("docstring") std::wostringstream "

STL class. ";


// File: classXapian_1_1WritableDatabase.xml
%feature("docstring") Xapian::WritableDatabase "

This class provides read/write access to a database. ";

%feature("docstring")  Xapian::WritableDatabase::~WritableDatabase "

Destroy this handle on the database.

virtual Xapian::WritableDatabase::~WritableDatabase()

If there are no copies of this object remaining, the database will be
closed. If there are any transactions in progress these will be
aborted as if cancel_transaction had been called. ";

%feature("docstring")  Xapian::WritableDatabase::WritableDatabase "

Create an empty WritableDatabase.

Xapian::WritableDatabase::WritableDatabase() ";

%feature("docstring")  Xapian::WritableDatabase::WritableDatabase "

Open a database for update, automatically determining the database
backend to use.

Xapian::WritableDatabase::WritableDatabase(const std::string &path,
int action)

If the database is to be created, Xapian will try to create the
directory indicated by path if it doesn't already exist (but only the
leaf directory, not recursively).

Parameters:
-----------

path:  directory that the database is stored in.

action:  one of:  Xapian::DB_CREATE_OR_OPEN open for read/write;
create if no db exists

Xapian::DB_CREATE create new database; fail if db exists

Xapian::DB_CREATE_OR_OVERWRITE overwrite existing db; create if none
exists

Xapian::DB_OPEN open for read/write; fail if no db exists

Parameters:
-----------

Xapian::DatabaseCorruptError:  will be thrown if the database is in a
corrupt state.

Xapian::DatabaseLockError:  will be thrown if a lock couldn't be
acquired on the database. ";

%feature("docstring")  Xapian::WritableDatabase::WritableDatabase "

Copying is allowed.

Xapian::WritableDatabase::WritableDatabase(const WritableDatabase
&other)

The internals are reference counted, so copying is cheap. ";

%feature("docstring")  Xapian::WritableDatabase::commit "

Commit any pending modifications made to the database.

void Xapian::WritableDatabase::commit()

For efficiency reasons, when performing multiple updates to a database
it is best (indeed, almost essential) to make as many modifications as
memory will permit in a single pass through the database. To ensure
this, Xapian batches up modifications.

This method may be called at any time to commit any pending
modifications to the database.

If any of the modifications fail, an exception will be thrown and the
database will be left in a state in which each separate addition,
replacement or deletion operation has either been fully performed or
not performed at all: it is then up to the application to work out
which operations need to be repeated.

It's not valid to call commit() within a transaction.

Beware of calling commit() too frequently: this will make indexing
take much longer.

Note that commit() need not be called explicitly: it will be called
automatically when the database is closed, or when a sufficient number
of modifications have been made. By default, this is every 10000
documents added, deleted, or modified. This value is rather
conservative, and if you have a machine with plenty of memory, you can
improve indexing throughput dramatically by setting
XAPIAN_FLUSH_THRESHOLD in the environment to a larger value.

Parameters:
-----------

Xapian::DatabaseError:  will be thrown if a problem occurs while
modifying the database.

Xapian::DatabaseCorruptError:  will be thrown if the database is in a
corrupt state. ";

%feature("docstring")  Xapian::WritableDatabase::flush "

Pre-1.1.0 name for commit().

void Xapian::WritableDatabase::flush()

Use commit() instead in new code. This alias may be deprecated in the
future. ";

%feature("docstring")  Xapian::WritableDatabase::begin_transaction "

Begin a transaction.

void Xapian::WritableDatabase::begin_transaction(bool flushed=true)

In Xapian a transaction is a group of modifications to the database
which are linked such that either all will be applied simultaneously
or none will be applied at all. Even in the case of a power failure,
this characteristic should be preserved (as long as the filesystem
isn't corrupted, etc).

A transaction is started with begin_transaction() and can either be
committed by calling commit_transaction() or aborted by calling
cancel_transaction().

By default, a transaction implicitly calls commit() before and after
so that the modifications stand and fall without affecting
modifications before or after.

The downside of these implicit calls to commit() is that small
transactions can harm indexing performance in the same way that
explicitly calling commit() frequently can.

If you're applying atomic groups of changes and only wish to ensure
that each group is either applied or not applied, then you can prevent
the automatic commit() before and after the transaction by starting
the transaction with begin_transaction(false). However, if
cancel_transaction is called (or if commit_transaction isn't called
before the WritableDatabase object is destroyed) then any changes
which were pending before the transaction began will also be
discarded.

Transactions aren't currently supported by the InMemory backend.

Parameters:
-----------

Xapian::UnimplementedError:  will be thrown if transactions are not
available for this database type.

Xapian::InvalidOperationError:  will be thrown if this is called at an
invalid time, such as when a transaction is already in progress. ";

%feature("docstring")  Xapian::WritableDatabase::commit_transaction "

Complete the transaction currently in progress.

void Xapian::WritableDatabase::commit_transaction()

If this method completes successfully and this is a flushed
transaction, all the database modifications made during the
transaction will have been committed to the database.

If an error occurs, an exception will be thrown, and none of the
modifications made to the database during the transaction will have
been applied to the database.

In all cases the transaction will no longer be in progress.

Parameters:
-----------

Xapian::DatabaseError:  will be thrown if a problem occurs while
modifying the database.

Xapian::DatabaseCorruptError:  will be thrown if the database is in a
corrupt state.

Xapian::InvalidOperationError:  will be thrown if a transaction is not
currently in progress.

Xapian::UnimplementedError:  will be thrown if transactions are not
available for this database type. ";

%feature("docstring")  Xapian::WritableDatabase::cancel_transaction "

Abort the transaction currently in progress, discarding the pending
modifications made to the database.

void Xapian::WritableDatabase::cancel_transaction()

If an error occurs in this method, an exception will be thrown, but
the transaction will be cancelled anyway.

Parameters:
-----------

Xapian::DatabaseError:  will be thrown if a problem occurs while
modifying the database.

Xapian::DatabaseCorruptError:  will be thrown if the database is in a
corrupt state.

Xapian::InvalidOperationError:  will be thrown if a transaction is not
currently in progress.

Xapian::UnimplementedError:  will be thrown if transactions are not
available for this database type. ";

%feature("docstring")  Xapian::WritableDatabase::add_document "

Add a new document to the database.

Xapian::docid Xapian::WritableDatabase::add_document(const
Xapian::Document &document)

This method adds the specified document to the database, returning a
newly allocated document ID. Automatically allocated document IDs come
from a per-database monotonically increasing counter, so IDs from
deleted documents won't be reused.

If you want to specify the document ID to be used, you should call
replace_document() instead.

Note that changes to the database won't be immediately committed to
disk; see commit() for more details.

As with all database modification operations, the effect is atomic:
the document will either be fully added, or the document fails to be
added and an exception is thrown (possibly at a later time when
commit() is called or the database is closed).

Parameters:
-----------

document:  The new document to be added.

The document ID of the newly added document.

Parameters:
-----------

Xapian::DatabaseError:  will be thrown if a problem occurs while
writing to the database.

Xapian::DatabaseCorruptError:  will be thrown if the database is in a
corrupt state. ";

%feature("docstring")  Xapian::WritableDatabase::delete_document "

Delete a document from the database.

void Xapian::WritableDatabase::delete_document(Xapian::docid did)

This method removes the document with the specified document ID from
the database.

Note that changes to the database won't be immediately committed to
disk; see commit() for more details.

As with all database modification operations, the effect is atomic:
the document will either be fully removed, or the document fails to be
removed and an exception is thrown (possibly at a later time when
commit() is called or the database is closed).

Parameters:
-----------

did:  The document ID of the document to be removed.

Parameters:
-----------

Xapian::DatabaseError:  will be thrown if a problem occurs while
writing to the database.

Xapian::DatabaseCorruptError:  will be thrown if the database is in a
corrupt state. ";

%feature("docstring")  Xapian::WritableDatabase::delete_document "

Delete any documents indexed by a term from the database.

void Xapian::WritableDatabase::delete_document(const std::string
&unique_term)

This method removes any documents indexed by the specified term from
the database.

A major use is for convenience when UIDs from another system are
mapped to terms in Xapian, although this method has other uses (for
example, you could add a \"deletion date\" term to documents at index
time and use this method to delete all documents due for deletion on a
particular date).

Parameters:
-----------

unique_term:  The term to remove references to.

Parameters:
-----------

Xapian::DatabaseError:  will be thrown if a problem occurs while
writing to the database.

Xapian::DatabaseCorruptError:  will be thrown if the database is in a
corrupt state. ";

%feature("docstring")  Xapian::WritableDatabase::replace_document "

Replace a given document in the database.

void Xapian::WritableDatabase::replace_document(Xapian::docid did,
const Xapian::Document &document)

This method replaces the document with the specified document ID. If
document ID did isn't currently used, the document will be added with
document ID did.

The monotonic counter used for automatically allocating document IDs
is increased so that the next automatically allocated document ID will
be did + 1. Be aware that if you use this method to specify a high
document ID for a new document, and also use
WritableDatabase::add_document(), Xapian may get to a state where this
counter wraps around and will be unable to automatically allocate
document IDs!

Note that changes to the database won't be immediately committed to
disk; see commit() for more details.

As with all database modification operations, the effect is atomic:
the document will either be fully replaced, or the document fails to
be replaced and an exception is thrown (possibly at a later time when
commit() is called or the database is closed).

Parameters:
-----------

did:  The document ID of the document to be replaced.

document:  The new document.

Parameters:
-----------

Xapian::DatabaseError:  will be thrown if a problem occurs while
writing to the database.

Xapian::DatabaseCorruptError:  will be thrown if the database is in a
corrupt state. ";

%feature("docstring")  Xapian::WritableDatabase::replace_document "

Replace any documents matching a term.

Xapian::docid Xapian::WritableDatabase::replace_document(const
std::string &unique_term, const Xapian::Document &document)

This method replaces any documents indexed by the specified term with
the specified document. If any documents are indexed by the term, the
lowest document ID will be used for the document, otherwise a new
document ID will be generated as for add_document.

One common use is to allow UIDs from another system to easily be
mapped to terms in Xapian. Note that this method doesn't automatically
add unique_term as a term, so you'll need to call
document.add_term(unique_term) first when using replace_document() in
this way.

Another possible use is to allow groups of documents to be marked for
later deletion - for example, you could add a \"deletion date\" term
to documents at index time and use this method to easily and
efficiently delete all documents due for deletion on a particular
date.

Note that changes to the database won't be immediately committed to
disk; see commit() for more details.

As with all database modification operations, the effect is atomic:
the document(s) will either be fully replaced, or the document(s) fail
to be replaced and an exception is thrown (possibly at a later time
when commit() is called or the database is closed).

Parameters:
-----------

unique_term:  The \"unique\" term.

document:  The new document.

The document ID that document was given.

Parameters:
-----------

Xapian::DatabaseError:  will be thrown if a problem occurs while
writing to the database.

Xapian::DatabaseCorruptError:  will be thrown if the database is in a
corrupt state. ";

%feature("docstring")  Xapian::WritableDatabase::add_spelling "

Add a word to the spelling dictionary.

void Xapian::WritableDatabase::add_spelling(const std::string &word,
Xapian::termcount freqinc=1) const

If the word is already present, its frequency is increased.

Parameters:
-----------

word:  The word to add.

freqinc:  How much to increase its frequency by (default 1). ";

%feature("docstring")  Xapian::WritableDatabase::remove_spelling "

Remove a word from the spelling dictionary.

void Xapian::WritableDatabase::remove_spelling(const std::string
&word, Xapian::termcount freqdec=1) const

The word's frequency is decreased, and if would become zero or less
then the word is removed completely.

Parameters:
-----------

word:  The word to remove.

freqdec:  How much to decrease its frequency by (default 1). ";

%feature("docstring")  Xapian::WritableDatabase::add_synonym "

Add a synonym for a term.

void Xapian::WritableDatabase::add_synonym(const std::string &term,
const std::string &synonym) const

If synonym is already a synonym for term, then no action is taken. ";

%feature("docstring")  Xapian::WritableDatabase::remove_synonym "

Remove a synonym for a term.

void Xapian::WritableDatabase::remove_synonym(const std::string &term,
const std::string &synonym) const

If synonym isn't a synonym for term, then no action is taken. ";

%feature("docstring")  Xapian::WritableDatabase::clear_synonyms "

Remove all synonyms for a term.

void Xapian::WritableDatabase::clear_synonyms(const std::string &term)
const

If term has no synonyms, no action is taken. ";

%feature("docstring")  Xapian::WritableDatabase::set_metadata "

Set the user-specified metadata associated with a given key.

void Xapian::WritableDatabase::set_metadata(const std::string &key,
const std::string &value)

This method sets the metadata value associated with a given key. If
there is already a metadata value stored in the database with the same
key, the old value is replaced. If you want to delete an existing item
of metadata, just set its value to the empty string.

User-specified metadata allows you to store arbitrary information in
the form of (key,tag) pairs.

There's no hard limit on the number of metadata items, or the size of
the metadata values. Metadata keys have a limited length, which
depends on the backend. We recommend limiting them to 200 bytes. Empty
keys are not valid, and specifying one will cause an exception.

Metadata modifications are committed to disk in the same way as
modifications to the documents in the database are: i.e.,
modifications are atomic, and won't be committed to disk immediately
(see commit() for more details). This allows metadata to be used to
link databases with versioned external resources by storing the
appropriate version number in a metadata item.

You can also use the metadata to store arbitrary extra information
associated with terms, documents, or postings by encoding the termname
and/or document id into the metadata key.

Parameters:
-----------

key:  The key of the metadata item to set.

value:  The value of the metadata item to set.

Parameters:
-----------

Xapian::DatabaseError:  will be thrown if a problem occurs while
writing to the database.

Xapian::DatabaseCorruptError:  will be thrown if the database is in a
corrupt state.

Xapian::InvalidArgumentError:  will be thrown if the key supplied is
empty.

Xapian::UnimplementedError:  will be thrown if the database backend in
use doesn't support user- specified metadata. ";

%feature("docstring")  Xapian::WritableDatabase::get_description "

Return a string describing this object.

std::string Xapian::WritableDatabase::get_description() const ";


// File: classstd_1_1wstring.xml
%feature("docstring") std::wstring "

STL class. ";


// File: classstd_1_1wstringstream.xml
%feature("docstring") std::wstringstream "

STL class. ";


// File: namespacestd.xml


// File: namespaceXapian.xml
%feature("docstring")  Xapian::Auto::sortable_serialise "

Convert a floating point number to a string, preserving sort order.

std::string Xapian::sortable_serialise(double value)

This method converts a floating point number to a string, suitable for
using as a value for numeric range restriction, or for use as a sort
key.

The conversion is platform independent.

The conversion attempts to ensure that, for any pair of values
supplied to the conversion algorithm, the result of comparing the
original values (with a numeric comparison operator) will be the same
as the result of comparing the resulting values (with a string
comparison operator). On platforms which represent doubles with the
precisions specified by IEEE_754, this will be the case: if the
representation of doubles is more precise, it is possible that two
very close doubles will be mapped to the same string, so will compare
equal.

Note also that both zero and -zero will be converted to the same
representation: since these compare equal, this satisfies the
comparison constraint, but it's worth knowing this if you wish to use
the encoding in some situation where this distinction matters.

Handling of NaN isn't (currently) guaranteed to be sensible. ";

%feature("docstring")  Xapian::Auto::sortable_unserialise "

Convert a string encoded using sortable_serialise back to a floating
point number.

double Xapian::sortable_unserialise(const std::string &value)

This expects the input to be a string produced by
sortable_serialise(). If the input is not such a string, the value
returned is undefined (but no error will be thrown).

The result of the conversion will be exactly the value which was
supplied to  sortable_serialise() when making the string on platforms
which represent doubles with the precisions specified by IEEE_754, but
may be a different (nearby) value on other platforms. ";

%feature("docstring")  Xapian::Auto::version_string "

Report the version string of the library which the program is linked
with.

const char* Xapian::version_string()

This may be different to the version compiled against (given by
XAPIAN_VERSION) if shared libraries are being used. ";

%feature("docstring")  Xapian::Auto::major_version "

Report the major version of the library which the program is linked
with.

int Xapian::major_version()

This may be different to the version compiled against (given by
XAPIAN_MAJOR_VERSION) if shared libraries are being used. ";

%feature("docstring")  Xapian::Auto::minor_version "

Report the minor version of the library which the program is linked
with.

int Xapian::minor_version()

This may be different to the version compiled against (given by
XAPIAN_MINOR_VERSION) if shared libraries are being used. ";

%feature("docstring")  Xapian::Auto::revision "

Report the revision of the library which the program is linked with.

int Xapian::revision()

This may be different to the version compiled against (given by
XAPIAN_REVISION) if shared libraries are being used. ";


// File: namespaceXapian_1_1Auto.xml
%feature("docstring")  Xapian::Auto::open_stub "

Construct a Database object for a stub database file.

Database Xapian::Auto::open_stub(const std::string &file)

The stub database file contains serialised parameters for one or more
databases.

Parameters:
-----------

file:  pathname of the stub database file. ";

%feature("docstring")  Xapian::Auto::open_stub "

Construct a WritableDatabase object for a stub database file.

WritableDatabase Xapian::Auto::open_stub(const std::string &file, int
action)

The stub database file must contain serialised parameters for exactly
one database.

Parameters:
-----------

file:  pathname of the stub database file. ";


// File: namespaceXapian_1_1Brass.xml
%feature("docstring")  Xapian::Brass::open "

Construct a Database object for read-only access to a Brass database.

Database Xapian::Brass::open(const std::string &dir)

Parameters:
-----------

dir:  pathname of the directory containing the database. ";

%feature("docstring")  Xapian::Brass::open "

Construct a Database object for update access to a Brass database.

WritableDatabase Xapian::Brass::open(const std::string &dir, int
action, int block_size=8192)

Parameters:
-----------

dir:  pathname of the directory containing the database.

action:  determines handling of existing/non-existing database:
Xapian::DB_CREATE fail if database already exist, otherwise create new
database.

Xapian::DB_CREATE_OR_OPEN open existing database, or create new
database if none exists.

Xapian::DB_CREATE_OR_OVERWRITE overwrite existing database, or create
new database if none exists.

Xapian::DB_OPEN open existing database, failing if none exists.

block_size:  the Btree blocksize to use (in bytes), which must be a
power of two between 2048 and 65536 (inclusive). The default (also
used if an invalid value if passed) is 8192 bytes. This parameter is
ignored when opening an existing database. ";


// File: namespaceXapian_1_1Chert.xml
%feature("docstring")  Xapian::Chert::open "

Construct a Database object for read-only access to a Chert database.

Database Xapian::Chert::open(const std::string &dir)

Parameters:
-----------

dir:  pathname of the directory containing the database. ";

%feature("docstring")  Xapian::Chert::open "

Construct a Database object for update access to a Chert database.

WritableDatabase Xapian::Chert::open(const std::string &dir, int
action, int block_size=8192)

Parameters:
-----------

dir:  pathname of the directory containing the database.

action:  determines handling of existing/non-existing database:
Xapian::DB_CREATE fail if database already exist, otherwise create new
database.

Xapian::DB_CREATE_OR_OPEN open existing database, or create new
database if none exists.

Xapian::DB_CREATE_OR_OVERWRITE overwrite existing database, or create
new database if none exists.

Xapian::DB_OPEN open existing database, failing if none exists.

block_size:  the Btree blocksize to use (in bytes), which must be a
power of two between 2048 and 65536 (inclusive). The default (also
used if an invalid value if passed) is 8192 bytes. This parameter is
ignored when opening an existing database. ";


// File: namespaceXapian_1_1Flint.xml
%feature("docstring")  Xapian::Flint::open "

Construct a Database object for read-only access to a Flint database.

Database Xapian::Flint::open(const std::string &dir)

Parameters:
-----------

dir:  pathname of the directory containing the database. ";

%feature("docstring")  Xapian::Flint::open "

Construct a Database object for update access to a Flint database.

WritableDatabase Xapian::Flint::open(const std::string &dir, int
action, int block_size=8192)

Parameters:
-----------

dir:  pathname of the directory containing the database.

action:  determines handling of existing/non-existing database:
Xapian::DB_CREATE fail if database already exist, otherwise create new
database.

Xapian::DB_CREATE_OR_OPEN open existing database, or create new
database if none exists.

Xapian::DB_CREATE_OR_OVERWRITE overwrite existing database, or create
new database if none exists.

Xapian::DB_OPEN open existing database, failing if none exists.

block_size:  the Btree blocksize to use (in bytes), which must be a
power of two between 2048 and 65536 (inclusive). The default (also
used if an invalid value if passed) is 8192 bytes. This parameter is
ignored when opening an existing database. ";


// File: namespaceXapian_1_1InMemory.xml
%feature("docstring")  Xapian::InMemory::open "

Construct a WritableDatabase object for a new, empty InMemory
database.

WritableDatabase Xapian::InMemory::open()

Only a writable InMemory database can be created, since a read-only
one would always remain empty. ";


// File: namespaceXapian_1_1Remote.xml
%feature("docstring")  Xapian::Remote::open "

Construct a Database object for read-only access to a remote database
accessed via a TCP connection.

Database Xapian::Remote::open(const std::string &host, unsigned int
port, Xapian::timeout timeout=10000, Xapian::timeout
connect_timeout=10000)

Access to the remote database is via a TCP connection to the specified
host and port.

Parameters:
-----------

host:  hostname to connect to.

port:  port number to connect to.

timeout:  timeout in milliseconds. If this timeout is exceeded for any
individual operation on the remote database then
Xapian::NetworkTimeoutError is thrown. A timeout of 0 means don't
timeout. (Default is 10000ms, which is 10 seconds).

connect_timeout:  timeout to use when connecting to the server. If
this timeout is exceeded then Xapian::NetworkTimeoutError is thrown. A
timeout of 0 means don't timeout. (Default is 10000ms, which is 10
seconds). ";

%feature("docstring")  Xapian::Remote::open_writable "

Construct a WritableDatabase object for update access to a remote
database accessed via a TCP connection.

WritableDatabase Xapian::Remote::open_writable(const std::string
&host, unsigned int port, Xapian::timeout timeout=0, Xapian::timeout
connect_timeout=10000)

Access to the remote database is via a TCP connection to the specified
host and port.

Parameters:
-----------

host:  hostname to connect to.

port:  port number to connect to.

timeout:  timeout in milliseconds. If this timeout is exceeded for any
individual operation on the remote database then
Xapian::NetworkTimeoutError is thrown. (Default is 0, which means
don't timeout).

connect_timeout:  timeout to use when connecting to the server. If
this timeout is exceeded then Xapian::NetworkTimeoutError is thrown. A
timeout of 0 means don't timeout. (Default is 10000ms, which is 10
seconds). ";

%feature("docstring")  Xapian::Remote::open "

Construct a Database object for read-only access to a remote database
accessed via a program.

Database Xapian::Remote::open(const std::string &program, const
std::string &args, Xapian::timeout timeout=10000)

Access to the remote database is done by running an external program
and communicating with it on stdin/stdout.

Parameters:
-----------

program:  the external program to run.

args:  space-separated list of arguments to pass to program.

timeout:  timeout in milliseconds. If this timeout is exceeded for any
individual operation on the remote database then
Xapian::NetworkTimeoutError is thrown. A timeout of 0 means don't
timeout. (Default is 10000ms, which is 10 seconds). ";

%feature("docstring")  Xapian::Remote::open_writable "

Construct a WritableDatabase object for update access to a remote
database accessed via a program.

WritableDatabase Xapian::Remote::open_writable(const std::string
&program, const std::string &args, Xapian::timeout timeout=0)

Access to the remote database is done by running an external program
and communicating with it on stdin/stdout.

Parameters:
-----------

program:  the external program to run.

args:  space-separated list of arguments to pass to program.

timeout:  timeout in milliseconds. If this timeout is exceeded for any
individual operation on the remote database then
Xapian::NetworkTimeoutError is thrown. (Default is 0, which means
don't timeout). ";


// File: namespaceXapian_1_1Unicode.xml
%feature("docstring")  Xapian::Unicode::Internal::nonascii_to_utf8 "

Convert a single non-ASCII Unicode character to UTF-8.

unsigned Xapian::Unicode::nonascii_to_utf8(unsigned ch, char *buf)

This is intended mainly as a helper method for to_utf8().

The character ch (which must be > 128) is written to the buffer buf
and the length of the resultant UTF-8 character is returned.

NB buf must have space for (at least) 4 bytes. ";

%feature("docstring")  Xapian::Unicode::Internal::to_utf8 "

Convert a single Unicode character to UTF-8.

unsigned Xapian::Unicode::to_utf8(unsigned ch, char *buf)

The character ch is written to the buffer buf and the length of the
resultant UTF-8 character is returned.

NB buf must have space for (at least) 4 bytes. ";

%feature("docstring")  Xapian::Unicode::Internal::append_utf8 "

Append the UTF-8 representation of a single Unicode character to a
std::string.

void Xapian::Unicode::append_utf8(std::string &s, unsigned ch) ";

%feature("docstring")  Xapian::Unicode::Internal::get_category "

Return the category which a given Unicode character falls into.

category Xapian::Unicode::get_category(unsigned ch) ";

%feature("docstring")  Xapian::Unicode::Internal::is_wordchar "

Test if a given Unicode character is \"word character\".

bool Xapian::Unicode::is_wordchar(unsigned ch) ";

%feature("docstring")  Xapian::Unicode::Internal::is_whitespace "

Test if a given Unicode character is a whitespace character.

bool Xapian::Unicode::is_whitespace(unsigned ch) ";

%feature("docstring")  Xapian::Unicode::Internal::is_currency "

Test if a given Unicode character is a currency symbol.

bool Xapian::Unicode::is_currency(unsigned ch) ";

%feature("docstring")  Xapian::Unicode::Internal::tolower "

Convert a Unicode character to lowercase.

unsigned Xapian::Unicode::tolower(unsigned ch) ";

%feature("docstring")  Xapian::Unicode::Internal::toupper "

Convert a Unicode character to uppercase.

unsigned Xapian::Unicode::toupper(unsigned ch) ";

%feature("docstring")  Xapian::Unicode::Internal::tolower "

Convert a UTF-8 std::string to lowercase.

std::string Xapian::Unicode::tolower(const std::string &term) ";

%feature("docstring")  Xapian::Unicode::Internal::toupper "

Convert a UTF-8 std::string to uppercase.

std::string Xapian::Unicode::toupper(const std::string &term) ";


// File: namespaceXapian_1_1Unicode_1_1Internal.xml
%feature("docstring")  Xapian::Unicode::Internal::get_character_info "int Xapian::Unicode::Internal::get_character_info(unsigned ch) ";

%feature("docstring")  Xapian::Unicode::Internal::get_case_type "int
Xapian::Unicode::Internal::get_case_type(int info) ";

%feature("docstring")  Xapian::Unicode::Internal::get_category "category Xapian::Unicode::Internal::get_category(int info) ";

%feature("docstring")  Xapian::Unicode::Internal::get_delta "int
Xapian::Unicode::Internal::get_delta(int info) ";


// File: error_8h.xml


// File: version_8h.xml


// File: xapian_8h.xml


// File: compactor_8h.xml


// File: database_8h.xml


// File: dbfactory_8h.xml


// File: document_8h.xml


// File: enquire_8h.xml


// File: errorhandler_8h.xml


// File: expanddecider_8h.xml


// File: keymaker_8h.xml


// File: matchspy_8h.xml


// File: positioniterator_8h.xml


// File: postingiterator_8h.xml


// File: postingsource_8h.xml


// File: query_8h.xml


// File: queryparser_8h.xml


// File: registry_8h.xml


// File: stem_8h.xml


// File: termgenerator_8h.xml


// File: termiterator_8h.xml


// File: types_8h.xml


// File: unicode_8h.xml


// File: valueiterator_8h.xml


// File: valuesetmatchdecider_8h.xml


// File: weight_8h.xml


// File: deprecated.xml


// File: dir_6d03b6c8a4ca72c723d392470e8e08b7.xml


// File: dir_2a2a68904ebb7cebeba1fe6ce8760440.xml

