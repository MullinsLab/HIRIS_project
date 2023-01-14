# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

## isdb related models
class Integration(models.Model):
    source_name = models.ForeignKey('Source', models.DO_NOTHING, db_column='source_name')
    environment = models.TextField()
    sample = models.JSONField(blank=True, null=True)
    ltr = models.TextField(blank=True, null=True)
    landmark = models.TextField(blank=True, null=True)
    location = models.IntegerField(blank=True, null=True)
    orientation_in_landmark = models.TextField(blank=True, null=True)
    sequence = models.TextField(blank=True, null=True)
    sequence_junction = models.IntegerField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    info = models.JSONField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'integration'


class NcbiGene(models.Model):
    ncbi_gene_id = models.IntegerField(primary_key=True)
    name = models.TextField()
    type = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ncbi_gene'


class NcbiGeneLocation(models.Model):
    ncbi_gene = models.OneToOneField(NcbiGene, models.DO_NOTHING, primary_key=True)
    landmark = models.TextField()
    gene_start = models.IntegerField()
    gene_end = models.IntegerField()
    gene_range = models.TextField()  # This field type is a guess.
    gene_orientation = models.TextField()

    class Meta:
        managed = False
        db_table = 'ncbi_gene_location'
        unique_together = (('ncbi_gene', 'landmark', 'gene_start'),)


class Source(models.Model):
    source_name = models.CharField(primary_key=True, max_length=255)
    document = models.JSONField(blank=True, null=True)
    revision = models.JSONField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'source'


"""
## django related models for reference only
class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


"""