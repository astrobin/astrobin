# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Solution.fieldunits'
        db.delete_column('astrobin_apps_platesolving_solution', 'fieldunits')

        # Deleting field 'Solution.ra_center_hms'
        db.delete_column('astrobin_apps_platesolving_solution', 'ra_center_hms')

        # Deleting field 'Solution.fieldw'
        db.delete_column('astrobin_apps_platesolving_solution', 'fieldw')

        # Deleting field 'Solution.fieldh'
        db.delete_column('astrobin_apps_platesolving_solution', 'fieldh')

        # Deleting field 'Solution.image_file'
        db.delete_column('astrobin_apps_platesolving_solution', 'image_file')

        # Deleting field 'Solution.dec_center_dms'
        db.delete_column('astrobin_apps_platesolving_solution', 'dec_center_dms')

        # Adding field 'Solution.ra'
        db.add_column('astrobin_apps_platesolving_solution', 'ra', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=14, blank=True), keep_default=False)

        # Adding field 'Solution.dec'
        db.add_column('astrobin_apps_platesolving_solution', 'dec', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=3, blank=True), keep_default=False)

        # Adding field 'Solution.radius'
        db.add_column('astrobin_apps_platesolving_solution', 'radius', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=3, blank=True), keep_default=False)

        # Changing field 'Solution.orientation'
        db.alter_column('astrobin_apps_platesolving_solution', 'orientation', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=3))

        # Changing field 'Solution.pixscale'
        db.alter_column('astrobin_apps_platesolving_solution', 'pixscale', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=3))


    def backwards(self, orm):
        
        # Adding field 'Solution.fieldunits'
        db.add_column('astrobin_apps_platesolving_solution', 'fieldunits', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True), keep_default=False)

        # Adding field 'Solution.ra_center_hms'
        db.add_column('astrobin_apps_platesolving_solution', 'ra_center_hms', self.gf('django.db.models.fields.CharField')(max_length=12, null=True, blank=True), keep_default=False)

        # Adding field 'Solution.fieldw'
        db.add_column('astrobin_apps_platesolving_solution', 'fieldw', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=14, decimal_places=10, blank=True), keep_default=False)

        # Adding field 'Solution.fieldh'
        db.add_column('astrobin_apps_platesolving_solution', 'fieldh', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=14, decimal_places=10, blank=True), keep_default=False)

        # Adding field 'Solution.image_file'
        db.add_column('astrobin_apps_platesolving_solution', 'image_file', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True), keep_default=False)

        # Adding field 'Solution.dec_center_dms'
        db.add_column('astrobin_apps_platesolving_solution', 'dec_center_dms', self.gf('django.db.models.fields.CharField')(max_length=13, null=True, blank=True), keep_default=False)

        # Deleting field 'Solution.ra'
        db.delete_column('astrobin_apps_platesolving_solution', 'ra')

        # Deleting field 'Solution.dec'
        db.delete_column('astrobin_apps_platesolving_solution', 'dec')

        # Deleting field 'Solution.radius'
        db.delete_column('astrobin_apps_platesolving_solution', 'radius')

        # Changing field 'Solution.orientation'
        db.alter_column('astrobin_apps_platesolving_solution', 'orientation', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=14, decimal_places=10))

        # Changing field 'Solution.pixscale'
        db.alter_column('astrobin_apps_platesolving_solution', 'pixscale', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=14, decimal_places=10))


    models = {
        'astrobin_apps_platesolving.solution': {
            'Meta': {'object_name': 'Solution'},
            'dec': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '3', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'objects_in_field': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'orientation': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '3', 'blank': 'True'}),
            'pixscale': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '3', 'blank': 'True'}),
            'ra': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '14', 'blank': 'True'}),
            'radius': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '3', 'blank': 'True'}),
            'status': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'submission_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['astrobin_apps_platesolving']
