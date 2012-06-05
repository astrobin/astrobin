# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'GearAutoMerge.label'
        db.delete_column('astrobin_gearautomerge', 'label')

        # Adding field 'GearAutoMerge.make'
        db.add_column('astrobin_gearautomerge', 'make', self.gf('django.db.models.fields.CharField')(default='', max_length=128), keep_default=False)

        # Adding field 'GearAutoMerge.name'
        db.add_column('astrobin_gearautomerge', 'name', self.gf('django.db.models.fields.CharField')(default='', max_length=128), keep_default=False)

        # Changing field 'Gear.name'
        db.alter_column('astrobin_gear', 'name', self.gf('django.db.models.fields.CharField')(max_length=128))


    def backwards(self, orm):
        
        # Adding field 'GearAutoMerge.label'
        db.add_column('astrobin_gearautomerge', 'label', self.gf('django.db.models.fields.CharField')(default='', max_length=64), keep_default=False)

        # Deleting field 'GearAutoMerge.make'
        db.delete_column('astrobin_gearautomerge', 'make')

        # Deleting field 'GearAutoMerge.name'
        db.delete_column('astrobin_gearautomerge', 'name')

        # Changing field 'Gear.name'
        db.alter_column('astrobin_gear', 'name', self.gf('django.db.models.fields.CharField')(max_length=64))


    models = {
        'actstream.action': {
            'Meta': {'ordering': "('-timestamp',)", 'object_name': 'Action'},
            'action_object_content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'action_object'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'action_object_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'actor_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'actor'", 'to': "orm['contenttypes.ContentType']"}),
            'actor_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'target_content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'target'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'target_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'verb': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'astrobin.abpod': {
            'Meta': {'object_name': 'ABPOD'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Image']", 'unique': 'True'})
        },
        'astrobin.accessory': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Accessory', '_ormbases': ['astrobin.Gear']},
            'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'})
        },
        'astrobin.acquisition': {
            'Meta': {'object_name': 'Acquisition'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Image']"})
        },
        'astrobin.app': {
            'Meta': {'ordering': "['-created']", 'object_name': 'App'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'registrar': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'app_api_key'", 'to': "orm['auth.User']"}),
            'secret': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'})
        },
        'astrobin.appapikeyrequest': {
            'Meta': {'ordering': "['-created']", 'object_name': 'AppApiKeyRequest'},
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'registrar': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'app_api_key_request'", 'to': "orm['auth.User']"})
        },
        'astrobin.camera': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Camera', '_ormbases': ['astrobin.Gear']},
            'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'}),
            'pixel_size': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'sensor_height': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'sensor_width': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'astrobin.comment': {
            'Meta': {'object_name': 'Comment'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'comment': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Image']"}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['astrobin.Comment']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'astrobin.deepsky_acquisition': {
            'Meta': {'ordering': "['-saved_on', 'filter']", 'object_name': 'DeepSky_Acquisition', '_ormbases': ['astrobin.Acquisition']},
            'acquisition_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Acquisition']", 'unique': 'True', 'primary_key': 'True'}),
            'advanced': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'bias': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'binning': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'bortle': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
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
            'saved_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'sensor_cooling': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'temperature': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'})
        },
        'astrobin.favorite': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'Favorite'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Image']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'astrobin.filter': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Filter', '_ormbases': ['astrobin.Gear']},
            'bandwidth': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'astrobin.focalreducer': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'FocalReducer', '_ormbases': ['astrobin.Gear']},
            'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'})
        },
        'astrobin.gear': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Gear'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'make': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'master': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Gear']", 'null': 'True'}),
            'moderator_fixed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'astrobin.gearassistedmerge': {
            'Meta': {'object_name': 'GearAssistedMerge'},
            'cutoff': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '3', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'master': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assisted_master'", 'null': 'True', 'to': "orm['astrobin.Gear']"}),
            'slave': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assisted_slave'", 'null': 'True', 'to': "orm['astrobin.Gear']"})
        },
        'astrobin.gearautomerge': {
            'Meta': {'object_name': 'GearAutoMerge'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'make': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'master': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Gear']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'astrobin.gearcomment': {
            'Meta': {'object_name': 'GearComment'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'comment': ('django.db.models.fields.TextField', [], {}),
            'gear': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Gear']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['astrobin.GearComment']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'astrobin.gearmakeautorename': {
            'Meta': {'object_name': 'GearMakeAutoRename'},
            'rename_from': ('django.db.models.fields.CharField', [], {'max_length': '128', 'primary_key': 'True'}),
            'rename_to': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'astrobin.gearnevermerge': {
            'Meta': {'object_name': 'GearNeverMerge'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'master': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Gear']"})
        },
        'astrobin.gearuserinfo': {
            'Meta': {'unique_together': "(('gear', 'user'),)", 'object_name': 'GearUserInfo'},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'gear': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Gear']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'astrobin.image': {
            'Meta': {'ordering': "('-uploaded', '-id')", 'object_name': 'Image'},
            'accessories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Accessory']", 'null': 'True', 'blank': 'True'}),
            'allow_rating': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'animated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'binning': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'dec_center_dms': ('django.db.models.fields.CharField', [], {'max_length': '13', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'fieldh': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '14', 'decimal_places': '10', 'blank': 'True'}),
            'fieldunits': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'fieldw': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '14', 'decimal_places': '10', 'blank': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'filters': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Filter']", 'null': 'True', 'blank': 'True'}),
            'focal_length': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'focal_reducers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.FocalReducer']", 'null': 'True', 'blank': 'True'}),
            'guiding_cameras': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'guiding_cameras'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Camera']"}),
            'guiding_telescopes': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'guiding_telescopes'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Telescope']"}),
            'h': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'imaging_cameras': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'imaging_cameras'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Camera']"}),
            'imaging_telescopes': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'imaging_telescopes'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Telescope']"}),
            'is_final': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_solved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_stored': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_wip': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'license': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'link': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'link_to_fits': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'locations': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['astrobin.Location']", 'symmetrical': 'False'}),
            'mounts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Mount']", 'null': 'True', 'blank': 'True'}),
            'orientation': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '14', 'decimal_places': '10', 'blank': 'True'}),
            'original_ext': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'pixel_size': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'pixscale': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '14', 'decimal_places': '10', 'blank': 'True'}),
            'plot_is_overlay': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'presolve_information': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'ra_center_hms': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'}),
            'rating_score': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'rating_votes': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'scaling': ('django.db.models.fields.DecimalField', [], {'default': '100', 'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'software': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Software']", 'null': 'True', 'blank': 'True'}),
            'solar_system_main_subject': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'subject_type': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'subjects': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['astrobin.Subject']", 'symmetrical': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'uploaded': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'w': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'was_revision': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'watermark': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'watermark_opacity': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'watermark_position': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'watermark_text': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'})
        },
        'astrobin.imageoftheday': {
            'Meta': {'ordering': "['-date']", 'object_name': 'ImageOfTheDay'},
            'date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'image_of_the_day'", 'to': "orm['astrobin.Image']"})
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
            'h': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Image']"}),
            'is_final': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_solved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_stored': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'original_ext': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'uploaded': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'w': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'astrobin.location': {
            'Meta': {'object_name': 'Location'},
            'altitude': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'country': ('astrobin.fields.CountryField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lat_deg': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'lat_min': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'lat_sec': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'lat_side': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1'}),
            'lon_deg': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'lon_min': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'lon_sec': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'lon_side': ('django.db.models.fields.CharField', [], {'default': "'E'", 'max_length': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.UserProfile']", 'null': 'True'})
        },
        'astrobin.messiermarathon': {
            'Meta': {'ordering': "('messier_number',)", 'object_name': 'MessierMarathon'},
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Image']"}),
            'messier_number': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'})
        },
        'astrobin.messiermarathonnominations': {
            'Meta': {'ordering': "('messier_number', 'nominations')", 'unique_together': "(('messier_number', 'image'),)", 'object_name': 'MessierMarathonNominations'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Image']"}),
            'messier_number': ('django.db.models.fields.IntegerField', [], {}),
            'nominations': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'nominators': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'null': 'True', 'symmetrical': 'False'})
        },
        'astrobin.mount': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Mount', '_ormbases': ['astrobin.Gear']},
            'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'}),
            'max_payload': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'pe': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'})
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
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Software', '_ormbases': ['astrobin.Gear']},
            'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'astrobin.solarsystem_acquisition': {
            'Meta': {'object_name': 'SolarSystem_Acquisition', '_ormbases': ['astrobin.Acquisition']},
            'acquisition_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Acquisition']", 'unique': 'True', 'primary_key': 'True'}),
            'cmi': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'cmii': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'cmiii': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'focal_length': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fps': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '5', 'blank': 'True'}),
            'frames': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'seeing': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'transparency': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'astrobin.subject': {
            'Meta': {'object_name': 'Subject'},
            'catalog': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'dec': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '5', 'blank': 'True'}),
            'dim_majaxis': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'dim_minaxis': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mainId': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'mtype': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '64'}),
            'oid': ('django.db.models.fields.IntegerField', [], {}),
            'otype': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'ra': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '5', 'blank': 'True'})
        },
        'astrobin.subjectidentifier': {
            'Meta': {'object_name': 'SubjectIdentifier'},
            'catalog': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '64'}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'idlist'", 'to': "orm['astrobin.Subject']"})
        },
        'astrobin.telescope': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Telescope', '_ormbases': ['astrobin.Gear']},
            'aperture': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            'focal_length': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'astrobin.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'about': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'accessories': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'accessories'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Accessory']"}),
            'avatar': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'cameras': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'cameras'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Camera']"}),
            'default_license': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'default_watermark': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'default_watermark_opacity': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'default_watermark_position': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'default_watermark_text': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'filters': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'filters'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Filter']"}),
            'focal_reducers': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'focal_reducers'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.FocalReducer']"}),
            'follows': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'followers'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.UserProfile']"}),
            'follows_gear': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Gear']", 'null': 'True', 'blank': 'True'}),
            'follows_subjects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Subject']", 'null': 'True', 'blank': 'True'}),
            'hobbies': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True', 'blank': 'True'}),
            'mounts': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'mounts'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Mount']"}),
            'software': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'software'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Software']"}),
            'telescopes': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'telescopes'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Telescope']"}),
            'timezone': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
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
        },
        'djangoratings.vote': {
            'Meta': {'unique_together': "(('content_type', 'object_id', 'key', 'user', 'ip_address', 'cookie'),)", 'object_name': 'Vote'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votes'", 'to': "orm['contenttypes.ContentType']"}),
            'cookie': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_changed': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'score': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'votes'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'reviews.revieweditem': {
            'Meta': {'ordering': "('date_added',)", 'object_name': 'ReviewedItem'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reviews'", 'to': "orm['contenttypes.ContentType']"}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_changed': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'score': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reviews'", 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['astrobin']
