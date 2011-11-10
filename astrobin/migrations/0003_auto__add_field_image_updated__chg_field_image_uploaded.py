# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Image.updated'
        db.add_column('astrobin_image', 'updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True), keep_default=False)

        # Changing field 'Image.uploaded'
        db.alter_column('astrobin_image', 'uploaded', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))


    def backwards(self, orm):
        
        # Deleting field 'Image.updated'
        db.delete_column('astrobin_image', 'updated')

        # Changing field 'Image.uploaded'
        db.alter_column('astrobin_image', 'uploaded', self.gf('django.db.models.fields.DateTimeField')())


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
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'uploaded': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
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
            'hobbies': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True', 'blank': 'True'}),
            'locations': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Location']", 'null': 'True', 'blank': 'True'}),
            'mounts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Mount']", 'null': 'True', 'blank': 'True'}),
            'software': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Software']", 'null': 'True', 'blank': 'True'}),
            'telescopes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Telescope']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'website': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'})
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
