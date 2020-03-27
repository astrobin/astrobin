/*
 * Evaluation of astrometric solutions for the AstroBin/PixInsight image
 * annotation project.
 *
 * The routines included here are JavaScript adaptations of C++ classes and
 * routines pertaining to the PixInsight Class Library (PCL):
 * https://gitlab.com/pixinsight/PCL
 *
 * Copyright (C) 2020 Pleiades Astrophoto. All Rights Reserved.
 * Written by Juan Conejero (PTeam)
 *
 * Version 1.2.1
 * Released 2020 March 11
 */

/*
 * Base object for bicubic interpolation algorithm implementations.
 */
function BicubicInterpolationBase( M, cols, rows )
{
   this.M = M;
   this.cols = cols;
   this.rows = rows;

   /*
    * Initialize central grid coordinates and 4x4 interpolation matrix.
    */
   this.initXY = function( x, y )
   {
      // Central grid coordinates
      this.i1 = Math.min( Math.max( 0, Math.trunc( y ) ), this.rows-1 );
      this.j1 = Math.min( Math.max( 0, Math.trunc( x ) ), this.cols-1 );

      // Neighbor grid coordinates
      let j0 = this.j1 - 1;
      let i0 = this.i1 - 1;
      let j2 = this.j1 + 1;
      let i2 = this.i1 + 1;
      let j3 = this.j1 + 2;
      let i3 = this.i1 + 2;

      // Index of base matrix element
      let fp = i0*this.cols + j0;

      // Row 0
      if ( i0 < 0 )
         fp += this.cols;
      this.p0 = this.getRow( fp, j0, j2, j3 );

      // Row 1
      if ( i0 >= 0 )
         fp += this.cols;
      this.p1 = this.getRow( fp, j0, j2, j3 );

      // Row 2
      if ( i2 < this.rows )
         fp += this.cols;
      this.p2 = this.getRow( fp, j0, j2, j3 );

      // Row 3
      if ( i3 < this.rows )
         fp += this.cols;
      this.p3 = this.getRow( fp, j0, j2, j3 );
   };

   /*
    * Acquire a row of interpolation matrix elements with symmetric boundary
    * extensions.
    */
   this.getRow = function( fp, j0, j2, j3 )
   {
      let p = new Array( 4 );
      if ( j0 < 0 )
         ++fp;
      p[0] = this.M[fp];
      if ( j0 >= 0 )
         ++fp;
      p[1] = this.M[fp];

      if ( j2 < this.cols )
      {
         p[2] = this.M[++fp];
         if ( j3 < this.cols )
            ++fp;
         p[3] = this.M[fp];
      }
      else
      {
         p[2] = this.M[fp];
         p[3] = this.M[fp - 1];
      }
      return p;
   };
}

/*
 * Bicubic spline interpolation algorithm.
 *
 * M        The source matrix stored as an Array object in row order.
 *
 * cols     Number of matrix columns.
 *
 * rows     Number of matrix rows.
 *
 * clamp    Linear clamping threshold to prevent oscillations, in the [0,1]
 *          range. Optional parameter; the default value is 0.3.
 *
 * Reference:
 * Keys, R. G. (1981), Cubic Convolution Interpolation for Digital Image
 * Processing, IEEE Trans. Acoustics, Speech & Signal Proc., Vol. 29,
 * pp. 1153-1160.
 */
function BicubicSplineInterpolation( M, cols, rows, clamp )
{
   this.__base__ = BicubicInterpolationBase;
   this.__base__( M, cols, rows );

   this.clamp = (clamp === undefined || clamp < 0 || clamp > 1) ? 0.3 : clamp;

   /*
    * Returns an interpolated function value at x, y coordinates.
    */
   this.interpolate = function( x, y )
   {
      // Initialize grid coordinates and source matrix.
      this.initXY( x, y );

      // Cubic spline coefficients.
      let C = this.coefficients( x - this.j1 );

      // Interpolate neighbor rows.
      let c = [ this.spline( this.p0, C ),
                this.spline( this.p1, C ),
                this.spline( this.p2, C ),
                this.spline( this.p3, C ) ];

      // Interpolate result vertically
      return this.spline( c, this.coefficients( y - this.i1 ) );
   };

   /*
    * Returns an array of spline function coefficients for the specified value
    * of the independent variable.
    */
   this.coefficients = function( dx )
   {
      let dx2 = dx*dx;
      let dx3 = dx2*dx;
      let dx1_2 = dx/2;
      let dx2_2 = dx2/2;
      let dx3_2 = dx3/2;
      let dx22 = dx2 + dx2;
      let dx315 = dx3 + dx3_2;
      return [ dx2 - dx3_2 - dx1_2,
               dx315 - dx22 - dx2_2 + 1,
               dx22 - dx315 + dx1_2,
               dx3_2 - dx2_2 ];
   };

   /*
    * Interpolated value in one dimension (row or column).
    */
   this.spline = function( p, C )
   {
      // Unclamped code:
      //return p[0]*C[0] + p[1]*C[1] + p[2]*C[2] + p[3]*C[3];
      let f12 = p[1]*C[1] + p[2]*C[2];
      let f03 = p[0]*C[0] + p[3]*C[3];
      return (-f03 < f12*this.clamp) ? f12 + f03 : f12/(C[1] + C[2]);
   };
}

function EphemUtils()
{
}

/*
 * Computes the Julian date (JD) for a given date and time.
 *
 * t  The required time point. Can be either a Date object or a string in ISO
 *    8601 format.
 *
 * Returns the Julian date as {jdi,jdf}, where jdi and jdf are the integer and
 * fractional parts of the JD, respectively.
 *
 * Reference:
 * Meeus, Jean (1991), Astronomical Algorithms, Willmann-Bell, Inc., ch. 7.
 *
 * Algorithm modified to support negative Julian dates.
 */
EphemUtils.julianDate = function( t )
{
   if ( typeof( t ) === "string" )
      t = new Date( t );
   let year = t.getUTCFullYear();
   let month = t.getUTCMonth() + 1;
   let day = t.getUTCDate() + 1;
   let dayf = (t.getUTCHours() + (t.getUTCMinutes() + (t.getUTCSeconds() + t.getUTCMilliseconds()/1000)/60)/60)/24;

   if ( month <= 2 )
   {
      --year;
      month += 12;
   }

   let jdi = Math.trunc( Math.floor( 365.25*(year + 4716) ) ) + Math.trunc( 30.6001*(month + 1) ) + day - 1524;
   let jdf = dayf - 0.5;

   if ( jdi > 0 && jdf < 0  )
   {
      jdf += 1;
      --jdi;
   }
   else if ( jdi < 0 && jdf > 0 )
   {
      jdf -= 1;
      ++jdi;
   }

   if ( jdi > 2299160 || jdi == 2299160 && jdf >= 0.5 )
   {
      let a = Math.trunc( 0.01*year );
      jdi += 2 - a + (a >> 2);
   }

   return { jdi: jdi, jdf: jdf };
};

/*!
 * Returns the time interval in Julian centuries (36525 days) elapsed since
 * the standard J2000 epoch (JD 2451545.0 = 2000 January 1.5) for the specified
 * Julian date.
 */
EphemUtils.centuriesSinceJ2000 = function( jd )
{
   return (jd.jdi-2451545 + jd.jdf)/36525;
}

/*
 * Conversion from radians to degrees.
 */
EphemUtils.radiansToDegrees = function( rad )
{
   return 57.2957795130823208767981548141051700441964 * rad;
};

/*
 * Conversion from degrees to radians.
 */
EphemUtils.degreesToRadians = function( deg )
{
   return 0.0174532925199432957692369076848861272222 * deg;
};

/*
 * Database of TAI-UTC estimates (Delta AT).
 */
EphemUtils.deltaAT_data =
[
   // http://www.iausofa.org/ - SOFA release 2018-01-30
   [ 2436934.5,  1.4178180, 37300, 0.001296 ],
   // http://maia.usno.navy.mil/ser7/tai-utc.dat
   [ 2437300.5,  1.4228180, 37300, 0.001296 ],
   [ 2437512.5,  1.3728180, 37300, 0.001296 ],
   [ 2437665.5,  1.8458580, 37665, 0.0011232 ],
   [ 2438334.5,  1.9458580, 37665, 0.0011232 ],
   [ 2438395.5,  3.2401300, 38761, 0.001296 ],
   [ 2438486.5,  3.3401300, 38761, 0.001296 ],
   [ 2438639.5,  3.4401300, 38761, 0.001296 ],
   [ 2438761.5,  3.5401300, 38761, 0.001296 ],
   [ 2438820.5,  3.6401300, 38761, 0.001296 ],
   [ 2438942.5,  3.7401300, 38761, 0.001296 ],
   [ 2439004.5,  3.8401300, 38761, 0.001296 ],
   [ 2439126.5,  4.3131700, 39126, 0.002592 ],
   [ 2439887.5,  4.2131700, 39126, 0.002592 ],
   [ 2441317.5, 10.0 ],
   [ 2441499.5, 11.0 ],
   [ 2441683.5, 12.0 ],
   [ 2442048.5, 13.0 ],
   [ 2442413.5, 14.0 ],
   [ 2442778.5, 15.0 ],
   [ 2443144.5, 16.0 ],
   [ 2443509.5, 17.0 ],
   [ 2443874.5, 18.0 ],
   [ 2444239.5, 19.0 ],
   [ 2444786.5, 20.0 ],
   [ 2445151.5, 21.0 ],
   [ 2445516.5, 22.0 ],
   [ 2446247.5, 23.0 ],
   [ 2447161.5, 24.0 ],
   [ 2447892.5, 25.0 ],
   [ 2448257.5, 26.0 ],
   [ 2448804.5, 27.0 ],
   [ 2449169.5, 28.0 ],
   [ 2449534.5, 29.0 ],
   [ 2450083.5, 30.0 ],
   [ 2450630.5, 31.0 ],
   [ 2451179.5, 32.0 ],
   [ 2453736.5, 33.0 ],
   [ 2454832.5, 34.0 ],
   [ 2456109.5, 35.0 ],
   [ 2457204.5, 36.0 ],
   [ 2457754.5, 37.0 ]
];

/*
 * Returns the value of Delta AT, or the difference TAI-UTC, corresponding
 * to a time point specified as a Julian Date in the UTC timescale.
 *
 * UTC does not exist before 1960, so calling this function for a date before
 * that year is a conceptual error. For convenience, zero is returned in such
 * case instead of throwing an exception.
 *
 * The returned value is the difference TAI-UTC in seconds.
 */
EphemUtils.deltaAT = function( jd )
{
   let t = jd.jdi + jd.jdf;
   if ( t >= 2436934.5 ) // 1960
      for ( let i = EphemUtils.deltaAT_data.length; --i >= 0; )
      {
         let D = EphemUtils.deltaAT_data[i];
         if ( t >= D[0] )
         {
            if ( t >= 2441317.5 ) // 1972
               return D[1];
            return D[1] + (t - 2400000.5 - D[2])*D[3];
         }
      }

   return 0; // pre-UTC
};

/*
 * Mean obliquity of the ecliptic, IAU 2006 precession model.
 *
 * t  The required time point in the UTC timescale. Can be either a Date object
 *    or a string in ISO 8601 format.
 *
 * Returns the mean obliquity in radians.
 */
EphemUtils.obliquity = function( t )
{
   let jd = EphemUtils.julianDate( t );
   jd.jdf += (EphemUtils.deltaAT( jd ) + 32.184)/86400; // UTC -> TT
   let T = EphemUtils.centuriesSinceJ2000( jd );
   let T2 = T*T;
   let T3 = T2*T;
   let T4 = T3*T;
   let T5 = T4*T;
   return EphemUtils.degreesToRadians( (84381.406
                                       - T*46.836769
                                       - T2*0.0001831
                                       + T3*0.00200340
                                       - T4*0.000000576
                                       - T5*0.0000000434)/3600 );
};

/*
 * Returns an angle in degrees constrained to the range [0,360).
 */
EphemUtils.longitudeDegreesConstrained = function( deg )
{
   return (deg < 0) ? deg + 360 : ((deg < 360) ? deg : deg - 360);
};

/*
 * Conversion from spherical to rectangular coordinates.
 *
 * s  The spherical coordinates {lon,lat} in radians.
 *
 * Returns the rectangular coordinates {x,y,z}.
 */
EphemUtils.sphericalToRectangular = function( s )
{
   let slon = Math.sin( s.lon );
   let clon = Math.cos( s.lon );
   let slat = Math.sin( s.lat );
   let clat = Math.cos( s.lat );
   return { x: clon*clat,
            y: slon*clat,
            z: slat };
};

/*
 * Conversion from rectangular to spherical coordinates.
 *
 * r  The rectangular coordinates {x,y,z}.
 *
 * Returns the spherical coordinates {lon,lat} in radians.
 */
EphemUtils.rectangularToSpherical = function( r )
{
   let m2 = r.x*r.x + r.y*r.y;
   return { lon: (m2 == 0) ? 0 : Math.atan2( r.y, r.x ),
            lat: (r.z == 0) ? 0 : Math.atan2( r.z, Math.sqrt( m2 ) ) };
};

/*
 * Conversion from rectangular to spherical coordinates in degrees, with the
 * longitude constrained to the [0,360) range.
 *
 * r  The rectangular coordinates {x,y,z}.
 *
 * Returns the spherical coordinates {lon,lat} in degrees, 0 <= lon < 360.
 */
EphemUtils.rectangularToSphericalDegreesConstrained = function( r )
{
   let s = EphemUtils.rectangularToSpherical( r );
   s.lon = EphemUtils.longitudeDegreesConstrained( EphemUtils.radiansToDegrees( s.lon ) );
   s.lat = EphemUtils.radiansToDegrees( s.lat );
   return s;
};

/*
 * Conversion from rectangular equatorial to rectangular ecliptic coordinates.
 *
 * r        The rectangular equatorial coordinates {x,y,z}.
 *
 * se,ce    The sine and cosine of the obliquity of the ecliptic at the
 *          observation time.
 *
 * Returns the rectangular ecliptic coordinates {x,y,z}.
 */
EphemUtils.rectangularEquatorialToEcliptic = function( r, se, ce )
{
   return { x: r.x,
            y: r.y*ce + r.z*se,
            z: r.z*ce - r.y*se };
};

/*
 * Conversion from rectangular equatorial to ICRS rectangular galactic
 * coordinates.
 *
 * r        The rectangular equatorial coordinates {x,y,z}.
 *
 * Returns the ICRS rectangular galactic coordinates {x,y,z}.
 *
 * Reference:
 * Jia-Cheng Liu, Zi Zhu, and Hong Zhang, Reconsidering the galactic coordinate
 * system, Astronomy & Astrophysics manuscript no. AA2010, October 26, 2018.
 */
EphemUtils.rectangularEquatorialToGalactic = function( r )
{
   return { x: +0.494055821648*r.x - 0.054657353964*r.y - 0.445679169947*r.z,
            y: -0.872844082054*r.x - 0.484928636070*r.y + 0.746511167077*r.z,
            z: -0.867710446378*r.x - 0.198779490637*r.y + 0.455593344276*r.z };
};

/*
 * Interpolation of an astrometric solution given by matrices of celestial
 * coordinates sampled at discrete, regular image coordinate intervals.
 *
 * Ma       Matrix of sampled right ascension values in degrees. Sampled values
 *          should not include zero-crossing discontinuities, i.e. jumps from
 *          360 to zero degrees, which should be replaced by negative values or
 *          values >= 360, as necessary.
 *
 * Md       Matrix of sampled declination values in degrees.
 *
 * x0, y0, x1, y1    The rectangular region (left, top, right, bottom) where
 *          equatorial spherical coordinates have been sampled in image
 *          coordinates.
 *
 * delta    Sampling distance, or the distance in image pixels between adjacent
 *          matrix columns or rows.
 *
 * date     The observation time in the UTC timescale. Can be a Date object or
 *          a string in ISO 8601 format. If not specified or undefined,
 *          ecliptic coordinates won't be calculated by coordinate
 *          interpolation methods.
 *
 * scale    The scale of interpolation. For example, if this object is going to
 *          be used to interpolate coordinates over an image that has been
 *          reduced to one half of the original image dimensions (given by the
 *          x0...y1 parameters), scale should be specified as 0.5. This scale
 *          will be used to select a suitable decimal precision for string
 *          representations of coordinates generated by the
 *          CoordinateInterpolation.interpolateAsText() method. If not
 *          specified or undefined, the default scale is 1.
 */
function CoordinateInterpolation( Ma, Md, x0, y0, x1, y1, delta, date, scale )
{
   this.Ma = Ma;
   this.Md = Md;

   this.x0 = Math.min( x0, x1 );
   this.x1 = Math.max( x0, x1 );
   this.y0 = Math.min( y0, y1 );
   this.y1 = Math.max( y0, y1 );
   this.delta = delta;
   this.date = date;
   if ( this.date !== undefined )
   {
      let eps = EphemUtils.obliquity( this.date );
      this.se = Math.sin( eps );
      this.ce = Math.cos( eps );
   }

   let width = this.x1 - this.x0;
   let height = this.y1 - this.y0;
   this.rows = 1 + Math.trunc( height/this.delta ) + ((height%this.delta != 0) ? 1 : 0);
   this.cols = 1 + Math.trunc( width/this.delta ) + ((width%this.delta != 0) ? 1 : 0);

   if ( this.rows < 2 || this.cols < 2 )
      throw new Error( "CoordinateInterpolation: Insufficient interpolation space." );
   if ( Ma.length != this.rows*this.cols || Md.length != this.rows*this.cols )
      throw new Error( "CoordinateInterpolation: Invalid matrix dimensions." );

   this.Ia = new BicubicSplineInterpolation( this.Ma, this.cols, this.rows );
   this.Id = new BicubicSplineInterpolation( this.Md, this.cols, this.rows );

   /*
    * Interpolation of celestial equatorial spherical coordinates.
    *
    * x, y           Interpolation point in image coordinates.
    *
    * withGalactic   If specified as true, calculate ICRS galactic coordinates.
    *
    * withEcliptic   If specified as true, calculate ecliptic coordinates for
    *                the date and time of observation. If no observation time
    *                has been specified for this object, this option will be
    *                ignored.
    *
    * Returns { alpha, delta, l, b, lambda, beta }, where alpha is the right
    * ascension in the range [0,360) and delta is the declination in [-90,+90],
    * both values expressed in degrees.
    *
    * If withGalactic has been specified as true, l and b are the ICRS galactic
    * longitude and latitude, respectively in the ranges [0,360) and [-90,+90]
    * in degrees. Otherwise the l and b properties will be undefined.
    *
    * If withEcliptic has been specified as true and this object knowns the
    * observation time (because it was specified upon construction), lambda and
    * beta are the ecliptic longitude and latitude at the time of observation,
    * respectively in the ranges [0,360) and [-90,+90] in degrees. Otherwise
    * the lambda and beta properties will be undefined.
    */
   this.interpolate = function( x, y, withGalactic, withEcliptic )
   {
      let fx = (x - this.x0)/this.delta;
      let fy = (y - this.y0)/this.delta;
      let alpha = EphemUtils.longitudeDegreesConstrained( this.Ia.interpolate( fx, fy ) );
      let delta = this.Id.interpolate( fx, fy );
      let retVal = { alpha: alpha, delta: delta };
      if ( withGalactic || withEcliptic && this.date !== undefined )
      {
         let s = { lon: EphemUtils.degreesToRadians( alpha ),
                   lat: EphemUtils.degreesToRadians( delta ) };
         let r = EphemUtils.sphericalToRectangular( s );
         if ( withGalactic )
         {
            let g = EphemUtils.rectangularToSphericalDegreesConstrained(
                        EphemUtils.rectangularEquatorialToGalactic( r ) );
            retVal.l = g.lon;
            retVal.b = g.lat;
         }
         if ( withEcliptic )
            if ( this.date !== undefined )
            {
               let e = EphemUtils.rectangularToSphericalDegreesConstrained(
                           EphemUtils.rectangularEquatorialToEcliptic( r, this.se, this.ce ) );
               retVal.lambda = e.lon;
               retVal.beta = e.lat;
            }
      }
      return retVal;
   };

   /*
    * Interpolation of celestial equatorial spherical coordinates represented
    * as formatted strings.
    *
    * x, y           Interpolation point in image coordinates.
    *
    * units          Whether to include unit characters in the sexagesimal
    *                representations. Enabled by default if not specified.
    *
    * withGalactic   If specified as true, calculate ICRS galactic coordinates.
    *
    * withEcliptic   If specified as true, calculate ecliptic coordinates for
    *                the date and time of observation. If no observation time
    *                has been specified for this object, this option will be
    *                ignored.
    *
    * Returns { alpha, delta, l, b, lambda, beta }, where the properties are
    * textual sexagesimal representations of right ascension in hours,
    * declination in degrees, galactic longitude and latitude in degrees, and
    * ecliptic longitude and latitude in degrees, respectively. The
    * representations have three items (degrees|hours, minutes and seconds) and
    * the decimal precision of the last item is selected automatically as a
    * function of image scale, taking into account the 'scale' argument
    * specified upon object construction, or its default value of 1.
    *
    * If withGalactic has not been specified as true, the l and b properties
    * will be undefined.
    *
    * If withEcliptic has not been specified as true, or if this object does
    * not know the observation time (because it was not specified upon
    * construction), the lambda and beta properties will be undefined.
    */
   this.interpolateAsText = function( x, y, units, withGalactic, withEcliptic )
   {
      if ( units === undefined )
         units = true;
      let q = this.interpolate( x, y, withGalactic, withEcliptic );
      let retVal = { alpha: this.angleString( q.alpha/15, 24/*range*/, false/*sign*/, this.precision+1, units ),
                     delta: this.angleString( q.delta, 0/*range*/, true/*sign*/, this.precision, units ) };
      if ( q.l !== undefined )
      {
         retVal.l = this.angleString( q.l, 360/*range*/, false/*sign*/, this.precision, units );
         retVal.b = this.angleString( q.b, 0/*range*/, true/*sign*/, this.precision, units );
      }
      if ( q.lambda !== undefined )
      {
         retVal.lambda = this.angleString( q.lambda, 360/*range*/, false/*sign*/, this.precision, units );
         retVal.beta = this.angleString( q.beta, 0/*range*/, true/*sign*/, this.precision, units );
      }
      return retVal;
   };

   // Determine an automatic coordinate precision appropriate for the scale of
   // the image in arcseconds per pixel.
   if ( scale === undefined || scale <= 0 )
      scale = 1;
   let q1 = this.interpolate( (this.x0 + this.x1)/2, (this.y0 + this.y1)/2 );
   let q2 = this.interpolate( (this.x0 + this.x1)/2 + 1/scale, (this.y0 + this.y1)/2 + 1/scale );
   let d = 3600*Math.min( Math.abs( q2.alpha - q1.alpha ), Math.abs( q2.delta - q1.delta ) );
   this.precision = (d >= 2) ? 0 : ((d >= 1) ? 1 : 2);

   /*
    * Generates a sexagesimal textual representation of the specified angle.
    *
    * angle    The angle in degrees or time units.
    *
    * range    The expected range. Should be 24 for time units,
    *          180 for longitudes, and 90 for latitudes.
    *
    * sign     Whether to include a sign character, even for positive values.
    *
    * precision   Number of decimal digits represented in the last item.
    *
    * units    Whether to include unit characters.
    */
   this.angleString = function( angle, range, sign, precision, units )
   {
      function decimalToSexagesimal( d )
      {
         let t1 = Math.abs( d );
         let t2 = (t1 - Math.trunc( t1 ))*60;
         return [ (d < 0) ? -1 : +1,
                  Math.trunc( t1 ),
                  Math.trunc( t2 ),
                  (t2 - Math.trunc( t2 ))*60 ];
      }

      function roundTo( x, n )
      {
         let p = Math.pow( 10, n );
         return Math.round( p*x )/p;
      }

      function zeroPadded( x, n )
      {
         let s = x.toString();
         while ( s.length < n )
            s = '0' + s;
         return s;
      }

      function whitePadded( x, n )
      {
         let s = x.toString();
         while ( s.length < n )
            s = ' ' + s;
         return s;
      }

      let d = decimalToSexagesimal( angle );
      let dd = d[1];
      let mm = d[2];
      let ss = d[3];
      ss = roundTo( ss, precision );
      if ( ss == 60 )
      {
         ss = 0;
         if ( ++mm == 60 )
         {
            mm = 0;
            if ( ++dd == range )
               dd = 0;
         }
      }
      let ff;
      if ( precision > 0 )
      {
         let si = Math.trunc( ss );
         ff = Math.round( (ss - si)*Math.pow( 10, precision ) );
         ss = si;
      }

      let dw = (range >= 100) ? 3 : 2;
      let sw = 2 + ((precision > 0) ? 1 : 0) + precision;
      let du = ' ', mu = ' ', su = '';
      if ( units )
         if ( range == 24 )
         {
            du = 'h';
            mu = 'm';
            su = 's';
         }
         else
         {
            du = '\u00B0';
            mu = '\u2032';
            su = '\u2033';
         }
      let result = (sign ? ((d[0] < 0) ? '-' : '+') : '')
                 + whitePadded( dd, dw )
                 + du
                 + zeroPadded( mm, 2 )
                 + mu
                 + zeroPadded( ss, 2 );
      if ( units )
         result += su;
      if ( precision > 0 )
         result += '.' + zeroPadded( ff, precision );
      return result;
   };
}
