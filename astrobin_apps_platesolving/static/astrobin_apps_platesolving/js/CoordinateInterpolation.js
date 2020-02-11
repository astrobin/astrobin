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
 * Reference: Keys, R. G. (1981), Cubic Convolution Interpolation for Digital
 * Image Processing, IEEE Trans. Acoustics, Speech & Signal Proc., Vol. 29,
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
 */
function CoordinateInterpolation( Ma, Md, x0, y0, x1, y1, delta )
{
   this.Ma = Ma;
   this.Md = Md;

   this.x0 = Math.min( x0, x1 );
   this.x1 = Math.max( x0, x1 );
   this.y0 = Math.min( y0, y1 );
   this.y1 = Math.max( y0, y1 );
   this.delta = delta;

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
    * x, y  Interpolation point in image coordinates.
    *
    * Returns { alpha, delta }, where alpha is the right ascension in the range
    * [0,360) and delta is the declination in [-90,+90], both values expressed
    * in degrees.
    */
   this.interpolate = function( x, y )
   {
      let fx = (x - this.x0)/this.delta;
      let fy = (y - this.y0)/this.delta;
      let alpha = this.Ia.interpolate( fx, fy );
      let delta = this.Id.interpolate( fx, fy );
      if ( alpha < 0 )
         alpha += 360;
      else if ( alpha >= 360 )
         alpha -= 360;
      return { alpha: alpha, delta: delta };
   };

   /*
    * Interpolation of celestial equatorial spherical coordinates represented
    * as formatted strings.
    *
    * x, y     Interpolation point in image coordinates.
    *
    * units    Whether to include unit characters in the sexagesimal
    *          representations. Enabled by default if not specified.
    *
    * Returns { alpha, delta }, where both properties are textual sexagesimal
    * representations of right ascension in hours and declination in degrees,
    * respectively. The representations have three items (degrees|hours,
    * minutes and seconds) and the decimal precision of the last item is
    * selected automatically as a function of image scale.
    */
   this.interpolateAsText = function( x, y, units )
   {
      if ( units === undefined )
         units = true;
      let q = this.interpolate( x, y );
      return { alpha: this.angleString( q.alpha/15, 24/*range*/, false/*sign*/, this.precision+1, units ),
               delta: this.angleString( q.delta, 0/*range*/, true/*sign*/, this.precision, units ) };
   };

   // Determine an automatic coordinate precision, appropriate for the scale of
   // the image in arcseconds per pixel.
   let q1 = this.interpolate( (this.x0 + this.x1)/2, (this.y0 + this.y1)/2 );
   let q2 = this.interpolate( (this.x0 + this.x1)/2 + 1, (this.y0 + this.y1)/2 + 1 );
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
                 + zeroPadded( dd, dw )
                 + du
                 + zeroPadded( mm, 2 )
                 + mu
                 + zeroPadded( roundTo( ss, precision ), sw );
      if ( units )
         if ( precision > 0 )
            result = result.replace( '.', su+'.' );
         else
            result += su;
      return result;
   };
}
