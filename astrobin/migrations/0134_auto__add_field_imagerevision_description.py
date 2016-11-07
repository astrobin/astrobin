# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'ImageRevision.description'
        db.add_column(u'astrobin_imagerevision', 'description',
                      self.gf('django.db.models.fields.TextField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'ImageRevision.description'
        db.delete_column(u'astrobin_imagerevision', 'description')


    models = {
        'astrobin.accessory': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Accessory', '_ormbases': ['astrobin.Gear']},
            u'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'})
        },
        'astrobin.acquisition': {
            'Meta': {'object_name': 'Acquisition'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Image']"})
        },
        u'astrobin.app': {
            'Meta': {'ordering': "['-created']", 'object_name': 'App'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'registrar': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'app_api_key'", 'to': u"orm['auth.User']"}),
            'secret': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'})
        },
        u'astrobin.appapikeyrequest': {
            'Meta': {'ordering': "['-created']", 'object_name': 'AppApiKeyRequest'},
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'registrar': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'app_api_key_request'", 'to': u"orm['auth.User']"})
        },
        'astrobin.camera': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Camera', '_ormbases': ['astrobin.Gear']},
            u'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'}),
            'pixel_size': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'sensor_height': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'sensor_width': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'astrobin.collection': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('user', 'name'),)", 'object_name': 'Collection'},
            'cover': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Image']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_updated': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'images': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'collections'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Image']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        'astrobin.commercialgear': {
            'Meta': {'ordering': "['created']", 'object_name': 'CommercialGear'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_ar': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_de': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_el': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_es': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_fi': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_fr': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_it': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_ja': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_nl': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_pl': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_pt_BR': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_ru': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_sq': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_tr': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'featured_gear'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['astrobin.Image']"}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'producer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'commercial_gear'", 'to': u"orm['auth.User']"}),
            'proper_make': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'proper_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'tagline': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_ar': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_de': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_el': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_en': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_es': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_fi': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_fr': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_it': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_ja': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_nl': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_pl': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_pt_BR': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_ru': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_sq': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_tr': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'astrobin.deepsky_acquisition': {
            'Meta': {'ordering': "['-saved_on', 'filter']", 'object_name': 'DeepSky_Acquisition', '_ormbases': ['astrobin.Acquisition']},
            u'acquisition_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Acquisition']", 'unique': 'True', 'primary_key': 'True'}),
            'advanced': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'bias': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'binning': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'bortle': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'darks': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'duration': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Filter']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
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
        'astrobin.filter': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Filter', '_ormbases': ['astrobin.Gear']},
            'bandwidth': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            u'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'astrobin.focalreducer': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'FocalReducer', '_ormbases': ['astrobin.Gear']},
            u'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'})
        },
        'astrobin.gear': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Gear'},
            'commercial': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'base_gear'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['astrobin.CommercialGear']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'make': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'master': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Gear']", 'null': 'True'}),
            'moderator_fixed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'retailed': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['astrobin.RetailedGear']", 'symmetrical': 'False'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'astrobin.gearassistedmerge': {
            'Meta': {'object_name': 'GearAssistedMerge'},
            'cutoff': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '3', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'master': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assisted_master'", 'null': 'True', 'to': "orm['astrobin.Gear']"}),
            'slave': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assisted_slave'", 'null': 'True', 'to': "orm['astrobin.Gear']"})
        },
        'astrobin.gearhardmergeredirect': {
            'Meta': {'object_name': 'GearHardMergeRedirect'},
            'fro': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'to': ('django.db.models.fields.IntegerField', [], {})
        },
        'astrobin.gearmakeautorename': {
            'Meta': {'object_name': 'GearMakeAutoRename'},
            'rename_from': ('django.db.models.fields.CharField', [], {'max_length': '128', 'primary_key': 'True'}),
            'rename_to': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'astrobin.gearuserinfo': {
            'Meta': {'unique_together': "(('gear', 'user'),)", 'object_name': 'GearUserInfo'},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'gear': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Gear']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        'astrobin.globalstat': {
            'Meta': {'ordering': "['-date']", 'object_name': 'GlobalStat'},
            'date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'images': ('django.db.models.fields.IntegerField', [], {}),
            'integration': ('django.db.models.fields.IntegerField', [], {}),
            'users': ('django.db.models.fields.IntegerField', [], {})
        },
        'astrobin.image': {
            'Meta': {'ordering': "('-uploaded', '-id')", 'object_name': 'Image'},
            'accessories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Accessory']", 'null': 'True', 'blank': 'True'}),
            'allow_comments': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'animated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'filters': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Filter']", 'null': 'True', 'blank': 'True'}),
            'focal_reducers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.FocalReducer']", 'null': 'True', 'blank': 'True'}),
            'guiding_cameras': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'guiding_cameras'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Camera']"}),
            'guiding_telescopes': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'guiding_telescopes'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Telescope']"}),
            'h': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_file': ('django.db.models.fields.files.ImageField', [], {'max_length': '256', 'null': 'True'}),
            'imaging_cameras': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'imaging_cameras'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Camera']"}),
            'imaging_telescopes': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'imaging_telescopes'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Telescope']"}),
            'is_final': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_wip': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'license': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'link': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'link_to_fits': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'locations': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['astrobin.Location']", 'symmetrical': 'False'}),
            'moderated_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'images_moderated'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'moderated_when': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'moderator_decision': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'mounts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Mount']", 'null': 'True', 'blank': 'True'}),
            'objects_in_field': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'plot_is_overlay': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'published': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'software': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Software']", 'null': 'True', 'blank': 'True'}),
            'solar_system_main_subject': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'subject_type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'uploaded': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'w': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'watermark': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'watermark_opacity': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'watermark_position': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'watermark_size': ('django.db.models.fields.CharField', [], {'default': "'M'", 'max_length': '1'}),
            'watermark_text': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'})
        },
        'astrobin.imageoftheday': {
            'Meta': {'ordering': "['-date']", 'object_name': 'ImageOfTheDay'},
            'chosen_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'iotds_chosen'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'image_of_the_day'", 'to': "orm['astrobin.Image']"}),
            'runnerup_1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'iotd_runnerup_1'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['astrobin.Image']"}),
            'runnerup_2': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'iotd_runnerup_2'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['astrobin.Image']"})
        },
        'astrobin.imageofthedaycandidate': {
            'Meta': {'ordering': "['-date', 'position']", 'object_name': 'ImageOfTheDayCandidate'},
            'date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'image_of_the_day_candidate'", 'to': "orm['astrobin.Image']"}),
            'position': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'astrobin.imagerequest': {
            'Meta': {'ordering': "['-created']", 'object_name': 'ImageRequest', '_ormbases': ['astrobin.Request']},
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Image']"}),
            u'request_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Request']", 'unique': 'True', 'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '8'})
        },
        'astrobin.imagerevision': {
            'Meta': {'ordering': "('uploaded', '-id')", 'unique_together': "(('image', 'label'),)", 'object_name': 'ImageRevision'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'h': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['astrobin.Image']"}),
            'image_file': ('django.db.models.fields.files.ImageField', [], {'max_length': '256', 'null': 'True'}),
            'is_final': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'uploaded': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'w': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'astrobin.location': {
            'Meta': {'object_name': 'Location'},
            'altitude': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'country': ('astrobin.fields.CountryField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
        'astrobin.mount': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Mount', '_ormbases': ['astrobin.Gear']},
            u'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'}),
            'max_payload': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'pe': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'})
        },
        'astrobin.request': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Request'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'requester'", 'to': u"orm['auth.User']"}),
            'fulfilled': ('django.db.models.fields.BooleanField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'requestee'", 'to': u"orm['auth.User']"})
        },
        'astrobin.retailedgear': {
            'Meta': {'ordering': "['created']", 'object_name': 'RetailedGear'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'EUR'", 'max_length': '3'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'retailer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'retailed_gear'", 'to': u"orm['auth.User']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'astrobin.software': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Software', '_ormbases': ['astrobin.Gear']},
            u'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'astrobin.solarsystem_acquisition': {
            'Meta': {'object_name': 'SolarSystem_Acquisition', '_ormbases': ['astrobin.Acquisition']},
            u'acquisition_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Acquisition']", 'unique': 'True', 'primary_key': 'True'}),
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
        'astrobin.telescope': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Telescope', '_ormbases': ['astrobin.Gear']},
            'aperture': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            'focal_length': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            u'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'astrobin.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'about': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'accessories': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'accessories'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Accessory']"}),
            'autosubscribe': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'avatar': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'cameras': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'cameras'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Camera']"}),
            'company_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'company_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'company_website': ('django.db.models.fields.URLField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'default_frontpage_section': ('django.db.models.fields.CharField', [], {'default': "'global'", 'max_length': '16'}),
            'default_gallery_sorting': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'default_license': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'default_watermark': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'default_watermark_opacity': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'default_watermark_position': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'default_watermark_size': ('django.db.models.fields.CharField', [], {'default': "'M'", 'max_length': '1'}),
            'default_watermark_text': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'exclude_from_competitions': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'filters': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'filters'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Filter']"}),
            'focal_reducers': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'focal_reducers'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.FocalReducer']"}),
            'hobbies': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True', 'blank': 'True'}),
            'mounts': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'mounts'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Mount']"}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'premium_counter': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'real_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'receive_forum_emails': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'retailer_country': ('astrobin.fields.CountryField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'seen_realname': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'show_signatures': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'signature': ('django.db.models.fields.TextField', [], {'max_length': '1024', 'blank': 'True'}),
            'signature_html': ('django.db.models.fields.TextField', [], {'max_length': '1054', 'blank': 'True'}),
            'software': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'software'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Software']"}),
            'telescopes': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'telescopes'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Telescope']"}),
            'timezone': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'}),
            'website': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['astrobin']