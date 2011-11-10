# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Gear'
        db.create_table('astrobin_gear', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('astrobin', ['Gear'])

        # Adding model 'Telescope'
        db.create_table('astrobin_telescope', (
            ('gear_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['astrobin.Gear'], unique=True, primary_key=True)),
            ('focal_length', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('aperture', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('astrobin', ['Telescope'])

        # Adding model 'Mount'
        db.create_table('astrobin_mount', (
            ('gear_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['astrobin.Gear'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('astrobin', ['Mount'])

        # Adding model 'Camera'
        db.create_table('astrobin_camera', (
            ('gear_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['astrobin.Gear'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('astrobin', ['Camera'])

        # Adding model 'FocalReducer'
        db.create_table('astrobin_focalreducer', (
            ('gear_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['astrobin.Gear'], unique=True, primary_key=True)),
            ('ratio', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=3, decimal_places=2, blank=True)),
        ))
        db.send_create_signal('astrobin', ['FocalReducer'])

        # Adding model 'Software'
        db.create_table('astrobin_software', (
            ('gear_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['astrobin.Gear'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('astrobin', ['Software'])

        # Adding model 'Filter'
        db.create_table('astrobin_filter', (
            ('gear_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['astrobin.Gear'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('astrobin', ['Filter'])

        # Adding model 'Accessory'
        db.create_table('astrobin_accessory', (
            ('gear_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['astrobin.Gear'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('astrobin', ['Accessory'])

        # Adding model 'Subject'
        db.create_table('astrobin_subject', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('oid', self.gf('django.db.models.fields.IntegerField')()),
            ('ra', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=8, decimal_places=5, blank=True)),
            ('dec', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=8, decimal_places=5, blank=True)),
            ('mainId', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('otype', self.gf('django.db.models.fields.CharField')(max_length=16, null=True, blank=True)),
            ('mtype', self.gf('django.db.models.fields.CharField')(max_length=16, null=True, blank=True)),
            ('dim_majaxis', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2, blank=True)),
            ('dim_minaxis', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2, blank=True)),
        ))
        db.send_create_signal('astrobin', ['Subject'])

        # Adding model 'SubjectIdentifier'
        db.create_table('astrobin_subjectidentifier', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('identifier', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('subject', self.gf('django.db.models.fields.related.ForeignKey')(related_name='idlist', to=orm['astrobin.Subject'])),
        ))
        db.send_create_signal('astrobin', ['SubjectIdentifier'])

        # Adding model 'Location'
        db.create_table('astrobin_location', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('latitude', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=7, decimal_places=4, blank=True)),
            ('longitude', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=7, decimal_places=4, blank=True)),
            ('altitude', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('user_generated', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('astrobin', ['Location'])

        # Adding model 'Image'
        db.create_table('astrobin_image', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('original_ext', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('uploaded', self.gf('django.db.models.fields.DateTimeField')()),
            ('focal_length', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('pixel_size', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('is_stored', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_solved', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('rating_votes', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('rating_score', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
        ))
        db.send_create_signal('astrobin', ['Image'])

        # Adding M2M table for field subjects on 'Image'
        db.create_table('astrobin_image_subjects', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('image', models.ForeignKey(orm['astrobin.image'], null=False)),
            ('subject', models.ForeignKey(orm['astrobin.subject'], null=False))
        ))
        db.create_unique('astrobin_image_subjects', ['image_id', 'subject_id'])

        # Adding M2M table for field locations on 'Image'
        db.create_table('astrobin_image_locations', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('image', models.ForeignKey(orm['astrobin.image'], null=False)),
            ('location', models.ForeignKey(orm['astrobin.location'], null=False))
        ))
        db.create_unique('astrobin_image_locations', ['image_id', 'location_id'])

        # Adding M2M table for field imaging_telescopes on 'Image'
        db.create_table('astrobin_image_imaging_telescopes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('image', models.ForeignKey(orm['astrobin.image'], null=False)),
            ('telescope', models.ForeignKey(orm['astrobin.telescope'], null=False))
        ))
        db.create_unique('astrobin_image_imaging_telescopes', ['image_id', 'telescope_id'])

        # Adding M2M table for field guiding_telescopes on 'Image'
        db.create_table('astrobin_image_guiding_telescopes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('image', models.ForeignKey(orm['astrobin.image'], null=False)),
            ('telescope', models.ForeignKey(orm['astrobin.telescope'], null=False))
        ))
        db.create_unique('astrobin_image_guiding_telescopes', ['image_id', 'telescope_id'])

        # Adding M2M table for field mounts on 'Image'
        db.create_table('astrobin_image_mounts', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('image', models.ForeignKey(orm['astrobin.image'], null=False)),
            ('mount', models.ForeignKey(orm['astrobin.mount'], null=False))
        ))
        db.create_unique('astrobin_image_mounts', ['image_id', 'mount_id'])

        # Adding M2M table for field imaging_cameras on 'Image'
        db.create_table('astrobin_image_imaging_cameras', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('image', models.ForeignKey(orm['astrobin.image'], null=False)),
            ('camera', models.ForeignKey(orm['astrobin.camera'], null=False))
        ))
        db.create_unique('astrobin_image_imaging_cameras', ['image_id', 'camera_id'])

        # Adding M2M table for field guiding_cameras on 'Image'
        db.create_table('astrobin_image_guiding_cameras', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('image', models.ForeignKey(orm['astrobin.image'], null=False)),
            ('camera', models.ForeignKey(orm['astrobin.camera'], null=False))
        ))
        db.create_unique('astrobin_image_guiding_cameras', ['image_id', 'camera_id'])

        # Adding M2M table for field focal_reducers on 'Image'
        db.create_table('astrobin_image_focal_reducers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('image', models.ForeignKey(orm['astrobin.image'], null=False)),
            ('focalreducer', models.ForeignKey(orm['astrobin.focalreducer'], null=False))
        ))
        db.create_unique('astrobin_image_focal_reducers', ['image_id', 'focalreducer_id'])

        # Adding M2M table for field software on 'Image'
        db.create_table('astrobin_image_software', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('image', models.ForeignKey(orm['astrobin.image'], null=False)),
            ('software', models.ForeignKey(orm['astrobin.software'], null=False))
        ))
        db.create_unique('astrobin_image_software', ['image_id', 'software_id'])

        # Adding M2M table for field filters on 'Image'
        db.create_table('astrobin_image_filters', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('image', models.ForeignKey(orm['astrobin.image'], null=False)),
            ('filter', models.ForeignKey(orm['astrobin.filter'], null=False))
        ))
        db.create_unique('astrobin_image_filters', ['image_id', 'filter_id'])

        # Adding M2M table for field accessories on 'Image'
        db.create_table('astrobin_image_accessories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('image', models.ForeignKey(orm['astrobin.image'], null=False)),
            ('accessory', models.ForeignKey(orm['astrobin.accessory'], null=False))
        ))
        db.create_unique('astrobin_image_accessories', ['image_id', 'accessory_id'])

        # Adding model 'ImageRevision'
        db.create_table('astrobin_imagerevision', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['astrobin.Image'])),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('original_ext', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('uploaded', self.gf('django.db.models.fields.DateTimeField')()),
            ('is_stored', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_solved', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('astrobin', ['ImageRevision'])

        # Adding model 'Acquisition'
        db.create_table('astrobin_acquisition', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['astrobin.Image'])),
        ))
        db.send_create_signal('astrobin', ['Acquisition'])

        # Adding model 'DeepSky_Acquisition'
        db.create_table('astrobin_deepsky_acquisition', (
            ('acquisition_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['astrobin.Acquisition'], unique=True, primary_key=True)),
            ('is_synthetic', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('filter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['astrobin.Filter'], null=True, blank=True)),
            ('number', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('duration', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('iso', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('gain', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2, blank=True)),
            ('sensor_cooling', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('darks', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('flats', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('flat_darks', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('bias', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('mean_sqm', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2, blank=True)),
            ('mean_fwhm', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2, blank=True)),
        ))
        db.send_create_signal('astrobin', ['DeepSky_Acquisition'])

        # Adding model 'SolarSystem_Acquisition'
        db.create_table('astrobin_solarsystem_acquisition', (
            ('acquisition_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['astrobin.Acquisition'], unique=True, primary_key=True)),
            ('frames', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('fps', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('focal_length', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('cmi', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2, blank=True)),
            ('cmii', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2, blank=True)),
            ('cmiii', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2, blank=True)),
            ('seeing', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('transparency', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('time', self.gf('django.db.models.fields.CharField')(max_length=5, null=True, blank=True)),
        ))
        db.send_create_signal('astrobin', ['SolarSystem_Acquisition'])

        # Adding model 'ABPOD'
        db.create_table('astrobin_abpod', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['astrobin.Image'], unique=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('astrobin', ['ABPOD'])

        # Adding model 'Request'
        db.create_table('astrobin_request', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('from_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='requester', to=orm['auth.User'])),
            ('to_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='requestee', to=orm['auth.User'])),
            ('fulfilled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('astrobin', ['Request'])

        # Adding model 'ImageRequest'
        db.create_table('astrobin_imagerequest', (
            ('request_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['astrobin.Request'], unique=True, primary_key=True)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['astrobin.Image'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=8)),
        ))
        db.send_create_signal('astrobin', ['ImageRequest'])

        # Adding model 'LocationRequest'
        db.create_table('astrobin_locationrequest', (
            ('request_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['astrobin.Request'], unique=True, primary_key=True)),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['astrobin.Location'])),
        ))
        db.send_create_signal('astrobin', ['LocationRequest'])

        # Adding model 'UserProfile'
        db.create_table('astrobin_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('website', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('job', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('hobbies', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=8, null=True, blank=True)),
            ('avatar', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
        ))
        db.send_create_signal('astrobin', ['UserProfile'])

        # Adding M2M table for field locations on 'UserProfile'
        db.create_table('astrobin_userprofile_locations', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm['astrobin.userprofile'], null=False)),
            ('location', models.ForeignKey(orm['astrobin.location'], null=False))
        ))
        db.create_unique('astrobin_userprofile_locations', ['userprofile_id', 'location_id'])

        # Adding M2M table for field telescopes on 'UserProfile'
        db.create_table('astrobin_userprofile_telescopes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm['astrobin.userprofile'], null=False)),
            ('telescope', models.ForeignKey(orm['astrobin.telescope'], null=False))
        ))
        db.create_unique('astrobin_userprofile_telescopes', ['userprofile_id', 'telescope_id'])

        # Adding M2M table for field mounts on 'UserProfile'
        db.create_table('astrobin_userprofile_mounts', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm['astrobin.userprofile'], null=False)),
            ('mount', models.ForeignKey(orm['astrobin.mount'], null=False))
        ))
        db.create_unique('astrobin_userprofile_mounts', ['userprofile_id', 'mount_id'])

        # Adding M2M table for field cameras on 'UserProfile'
        db.create_table('astrobin_userprofile_cameras', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm['astrobin.userprofile'], null=False)),
            ('camera', models.ForeignKey(orm['astrobin.camera'], null=False))
        ))
        db.create_unique('astrobin_userprofile_cameras', ['userprofile_id', 'camera_id'])

        # Adding M2M table for field focal_reducers on 'UserProfile'
        db.create_table('astrobin_userprofile_focal_reducers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm['astrobin.userprofile'], null=False)),
            ('focalreducer', models.ForeignKey(orm['astrobin.focalreducer'], null=False))
        ))
        db.create_unique('astrobin_userprofile_focal_reducers', ['userprofile_id', 'focalreducer_id'])

        # Adding M2M table for field software on 'UserProfile'
        db.create_table('astrobin_userprofile_software', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm['astrobin.userprofile'], null=False)),
            ('software', models.ForeignKey(orm['astrobin.software'], null=False))
        ))
        db.create_unique('astrobin_userprofile_software', ['userprofile_id', 'software_id'])

        # Adding M2M table for field filters on 'UserProfile'
        db.create_table('astrobin_userprofile_filters', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm['astrobin.userprofile'], null=False)),
            ('filter', models.ForeignKey(orm['astrobin.filter'], null=False))
        ))
        db.create_unique('astrobin_userprofile_filters', ['userprofile_id', 'filter_id'])

        # Adding M2M table for field accessories on 'UserProfile'
        db.create_table('astrobin_userprofile_accessories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm['astrobin.userprofile'], null=False)),
            ('accessory', models.ForeignKey(orm['astrobin.accessory'], null=False))
        ))
        db.create_unique('astrobin_userprofile_accessories', ['userprofile_id', 'accessory_id'])

        # Adding M2M table for field follows on 'UserProfile'
        db.create_table('astrobin_userprofile_follows', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_userprofile', models.ForeignKey(orm['astrobin.userprofile'], null=False)),
            ('to_userprofile', models.ForeignKey(orm['astrobin.userprofile'], null=False))
        ))
        db.create_unique('astrobin_userprofile_follows', ['from_userprofile_id', 'to_userprofile_id'])


    def backwards(self, orm):
        
        # Deleting model 'Gear'
        db.delete_table('astrobin_gear')

        # Deleting model 'Telescope'
        db.delete_table('astrobin_telescope')

        # Deleting model 'Mount'
        db.delete_table('astrobin_mount')

        # Deleting model 'Camera'
        db.delete_table('astrobin_camera')

        # Deleting model 'FocalReducer'
        db.delete_table('astrobin_focalreducer')

        # Deleting model 'Software'
        db.delete_table('astrobin_software')

        # Deleting model 'Filter'
        db.delete_table('astrobin_filter')

        # Deleting model 'Accessory'
        db.delete_table('astrobin_accessory')

        # Deleting model 'Subject'
        db.delete_table('astrobin_subject')

        # Deleting model 'SubjectIdentifier'
        db.delete_table('astrobin_subjectidentifier')

        # Deleting model 'Location'
        db.delete_table('astrobin_location')

        # Deleting model 'Image'
        db.delete_table('astrobin_image')

        # Removing M2M table for field subjects on 'Image'
        db.delete_table('astrobin_image_subjects')

        # Removing M2M table for field locations on 'Image'
        db.delete_table('astrobin_image_locations')

        # Removing M2M table for field imaging_telescopes on 'Image'
        db.delete_table('astrobin_image_imaging_telescopes')

        # Removing M2M table for field guiding_telescopes on 'Image'
        db.delete_table('astrobin_image_guiding_telescopes')

        # Removing M2M table for field mounts on 'Image'
        db.delete_table('astrobin_image_mounts')

        # Removing M2M table for field imaging_cameras on 'Image'
        db.delete_table('astrobin_image_imaging_cameras')

        # Removing M2M table for field guiding_cameras on 'Image'
        db.delete_table('astrobin_image_guiding_cameras')

        # Removing M2M table for field focal_reducers on 'Image'
        db.delete_table('astrobin_image_focal_reducers')

        # Removing M2M table for field software on 'Image'
        db.delete_table('astrobin_image_software')

        # Removing M2M table for field filters on 'Image'
        db.delete_table('astrobin_image_filters')

        # Removing M2M table for field accessories on 'Image'
        db.delete_table('astrobin_image_accessories')

        # Deleting model 'ImageRevision'
        db.delete_table('astrobin_imagerevision')

        # Deleting model 'Acquisition'
        db.delete_table('astrobin_acquisition')

        # Deleting model 'DeepSky_Acquisition'
        db.delete_table('astrobin_deepsky_acquisition')

        # Deleting model 'SolarSystem_Acquisition'
        db.delete_table('astrobin_solarsystem_acquisition')

        # Deleting model 'ABPOD'
        db.delete_table('astrobin_abpod')

        # Deleting model 'Request'
        db.delete_table('astrobin_request')

        # Deleting model 'ImageRequest'
        db.delete_table('astrobin_imagerequest')

        # Deleting model 'LocationRequest'
        db.delete_table('astrobin_locationrequest')

        # Deleting model 'UserProfile'
        db.delete_table('astrobin_userprofile')

        # Removing M2M table for field locations on 'UserProfile'
        db.delete_table('astrobin_userprofile_locations')

        # Removing M2M table for field telescopes on 'UserProfile'
        db.delete_table('astrobin_userprofile_telescopes')

        # Removing M2M table for field mounts on 'UserProfile'
        db.delete_table('astrobin_userprofile_mounts')

        # Removing M2M table for field cameras on 'UserProfile'
        db.delete_table('astrobin_userprofile_cameras')

        # Removing M2M table for field focal_reducers on 'UserProfile'
        db.delete_table('astrobin_userprofile_focal_reducers')

        # Removing M2M table for field software on 'UserProfile'
        db.delete_table('astrobin_userprofile_software')

        # Removing M2M table for field filters on 'UserProfile'
        db.delete_table('astrobin_userprofile_filters')

        # Removing M2M table for field accessories on 'UserProfile'
        db.delete_table('astrobin_userprofile_accessories')

        # Removing M2M table for field follows on 'UserProfile'
        db.delete_table('astrobin_userprofile_follows')


    models = {
        'astrobin.abpod': {
            'Meta': {'object_name': 'ABPOD'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Image']", 'unique': 'True'})
        },
        'astrobin.accessory': {
            'Meta': {'object_name': 'Accessory', '_ormbases': ['astrobin.Gear']},
            'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'})
        },
        'astrobin.acquisition': {
            'Meta': {'object_name': 'Acquisition'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Image']"})
        },
        'astrobin.camera': {
            'Meta': {'object_name': 'Camera', '_ormbases': ['astrobin.Gear']},
            'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'})
        },
        'astrobin.deepsky_acquisition': {
            'Meta': {'ordering': "['filter']", 'object_name': 'DeepSky_Acquisition', '_ormbases': ['astrobin.Acquisition']},
            'acquisition_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Acquisition']", 'unique': 'True', 'primary_key': 'True'}),
            'bias': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'darks': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'duration': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Filter']", 'null': 'True', 'blank': 'True'}),
            'flat_darks': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'flats': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'gain': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'is_synthetic': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'iso': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mean_fwhm': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'mean_sqm': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sensor_cooling': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'astrobin.filter': {
            'Meta': {'object_name': 'Filter', '_ormbases': ['astrobin.Gear']},
            'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'})
        },
        'astrobin.focalreducer': {
            'Meta': {'object_name': 'FocalReducer', '_ormbases': ['astrobin.Gear']},
            'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'}),
            'ratio': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '3', 'decimal_places': '2', 'blank': 'True'})
        },
        'astrobin.gear': {
            'Meta': {'object_name': 'Gear'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'astrobin.image': {
            'Meta': {'ordering': "('-uploaded', '-id')", 'object_name': 'Image'},
            'accessories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Accessory']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'filters': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Filter']", 'null': 'True', 'blank': 'True'}),
            'focal_length': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'focal_reducers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.FocalReducer']", 'null': 'True', 'blank': 'True'}),
            'guiding_cameras': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'guiding_cameras'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Camera']"}),
            'guiding_telescopes': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'guiding_telescopes'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Telescope']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'imaging_cameras': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'imaging_cameras'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Camera']"}),
            'imaging_telescopes': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'imaging_telescopes'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Telescope']"}),
            'is_solved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_stored': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'locations': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Location']", 'null': 'True', 'blank': 'True'}),
            'mounts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Mount']", 'null': 'True', 'blank': 'True'}),
            'original_ext': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'pixel_size': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'rating_score': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'rating_votes': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'software': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Software']", 'null': 'True', 'blank': 'True'}),
            'subjects': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['astrobin.Subject']", 'symmetrical': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'uploaded': ('django.db.models.fields.DateTimeField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'astrobin.imagerequest': {
            'Meta': {'ordering': "['-created']", 'object_name': 'ImageRequest', '_ormbases': ['astrobin.Request']},
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Image']"}),
            'request_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Request']", 'unique': 'True', 'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '8'})
        },
        'astrobin.imagerevision': {
            'Meta': {'ordering': "('uploaded', '-id')", 'object_name': 'ImageRevision'},
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Image']"}),
            'is_solved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_stored': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'original_ext': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'uploaded': ('django.db.models.fields.DateTimeField', [], {})
        },
        'astrobin.location': {
            'Meta': {'object_name': 'Location'},
            'altitude': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '4', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '4', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user_generated': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'astrobin.locationrequest': {
            'Meta': {'ordering': "['-created']", 'object_name': 'LocationRequest', '_ormbases': ['astrobin.Request']},
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Location']"}),
            'request_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Request']", 'unique': 'True', 'primary_key': 'True'})
        },
        'astrobin.mount': {
            'Meta': {'object_name': 'Mount', '_ormbases': ['astrobin.Gear']},
            'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'})
        },
        'astrobin.request': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Request'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'requester'", 'to': "orm['auth.User']"}),
            'fulfilled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'requestee'", 'to': "orm['auth.User']"})
        },
        'astrobin.software': {
            'Meta': {'object_name': 'Software', '_ormbases': ['astrobin.Gear']},
            'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'})
        },
        'astrobin.solarsystem_acquisition': {
            'Meta': {'object_name': 'SolarSystem_Acquisition', '_ormbases': ['astrobin.Acquisition']},
            'acquisition_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Acquisition']", 'unique': 'True', 'primary_key': 'True'}),
            'cmi': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'cmii': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'cmiii': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'focal_length': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fps': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'frames': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'seeing': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'transparency': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'astrobin.subject': {
            'Meta': {'object_name': 'Subject'},
            'dec': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '5', 'blank': 'True'}),
            'dim_majaxis': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'dim_minaxis': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mainId': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'mtype': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'oid': ('django.db.models.fields.IntegerField', [], {}),
            'otype': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'ra': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '5', 'blank': 'True'})
        },
        'astrobin.subjectidentifier': {
            'Meta': {'object_name': 'SubjectIdentifier'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'idlist'", 'to': "orm['astrobin.Subject']"})
        },
        'astrobin.telescope': {
            'Meta': {'object_name': 'Telescope', '_ormbases': ['astrobin.Gear']},
            'aperture': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'focal_length': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'})
        },
        'astrobin.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'accessories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Accessory']", 'null': 'True', 'blank': 'True'}),
            'avatar': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'cameras': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Camera']", 'null': 'True', 'blank': 'True'}),
            'filters': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Filter']", 'null': 'True', 'blank': 'True'}),
            'focal_reducers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.FocalReducer']", 'null': 'True', 'blank': 'True'}),
            'follows': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'followers'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.UserProfile']"}),
            'hobbies': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True', 'blank': 'True'}),
            'locations': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Location']", 'null': 'True', 'blank': 'True'}),
            'mounts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Mount']", 'null': 'True', 'blank': 'True'}),
            'software': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Software']", 'null': 'True', 'blank': 'True'}),
            'telescopes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Telescope']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'website': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['astrobin']
