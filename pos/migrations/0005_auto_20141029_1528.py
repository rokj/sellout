# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pos', '0004_auto_20141029_1503'),
    ]

    operations = [
        migrations.CreateModel(
            name='BillCompany',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime_created', models.DateTimeField(editable=False, blank=True)),
                ('datetime_updated', models.DateTimeField(null=True, editable=False, blank=True)),
                ('name', models.CharField(max_length=200, verbose_name='Company name')),
                ('street', models.CharField(max_length=200, null=True, verbose_name='Street and house number', blank=True)),
                ('postcode', models.CharField(max_length=20, null=True, verbose_name='Postal code', blank=True)),
                ('city', models.CharField(max_length=50, null=True, verbose_name='City', blank=True)),
                ('state', models.CharField(max_length=50, null=True, verbose_name='State', blank=True)),
                ('country', models.CharField(blank=True, max_length=2, null=True, choices=[(b'AF', b'Afghanistan'), (b'AX', b'\xc3\x85land Islands'), (b'AL', b'Albania'), (b'DZ', b'Algeria'), (b'AS', b'American Samoa'), (b'AD', b'Andorra'), (b'AO', b'Angola'), (b'AI', b'Anguilla'), (b'AQ', b'Antarctica'), (b'AG', b'Antigua and Barbuda'), (b'AR', b'Argentina'), (b'AM', b'Armenia'), (b'AW', b'Aruba'), (b'AU', b'Australia'), (b'AT', b'Austria'), (b'AZ', b'Azerbaijan'), (b'BS', b'Bahamas'), (b'BH', b'Bahrain'), (b'BD', b'Bangladesh'), (b'BB', b'Barbados'), (b'BY', b'Belarus'), (b'BE', b'Belgium'), (b'BZ', b'Belize'), (b'BJ', b'Benin'), (b'BM', b'Bermuda'), (b'BT', b'Bhutan'), (b'BO', b'Bolivia, Plurinational State of'), (b'BQ', b'Bonaire, Sint Eustatius and Saba'), (b'BA', b'Bosnia and Herzegovina'), (b'BW', b'Botswana'), (b'BV', b'Bouvet Island'), (b'BR', b'Brazil'), (b'IO', b'British Indian Ocean Territory'), (b'BN', b'Brunei Darussalam'), (b'BG', b'Bulgaria'), (b'BF', b'Burkina Faso'), (b'BI', b'Burundi'), (b'KH', b'Cambodia'), (b'CM', b'Cameroon'), (b'CA', b'Canada'), (b'CV', b'Cape Verde'), (b'KY', b'Cayman Islands'), (b'CF', b'Central African Republic'), (b'TD', b'Chad'), (b'CL', b'Chile'), (b'CN', b'China'), (b'CX', b'Christmas Island'), (b'CC', b'Cocos (Keeling) Islands'), (b'CO', b'Colombia'), (b'KM', b'Comoros'), (b'CG', b'Congo'), (b'CD', b'Congo, the Democratic Republic of the'), (b'CK', b'Cook Islands'), (b'CR', b'Costa Rica'), (b'CI', b"C\xc3\xb4te d'Ivoire"), (b'HR', b'Croatia'), (b'CU', b'Cuba'), (b'CW', b'Cura\xc3\xa7ao'), (b'CY', b'Cyprus'), (b'CZ', b'Czech Republic'), (b'DK', b'Denmark'), (b'DJ', b'Djibouti'), (b'DM', b'Dominica'), (b'DO', b'Dominican Republic'), (b'EC', b'Ecuador'), (b'EG', b'Egypt'), (b'SV', b'El Salvador'), (b'GQ', b'Equatorial Guinea'), (b'ER', b'Eritrea'), (b'EE', b'Estonia'), (b'ET', b'Ethiopia'), (b'FK', b'Falkland Islands (Malvinas)'), (b'FO', b'Faroe Islands'), (b'FJ', b'Fiji'), (b'FI', b'Finland'), (b'FR', b'France'), (b'GF', b'French Guiana'), (b'PF', b'French Polynesia'), (b'TF', b'French Southern Territories'), (b'GA', b'Gabon'), (b'GM', b'Gambia'), (b'GE', b'Georgia'), (b'DE', b'Germany'), (b'GH', b'Ghana'), (b'GI', b'Gibraltar'), (b'GR', b'Greece'), (b'GL', b'Greenland'), (b'GD', b'Grenada'), (b'GP', b'Guadeloupe'), (b'GU', b'Guam'), (b'GT', b'Guatemala'), (b'GG', b'Guernsey'), (b'GN', b'Guinea'), (b'GW', b'Guinea-Bissau'), (b'GY', b'Guyana'), (b'HT', b'Haiti'), (b'HM', b'Heard Island and McDonald Islands'), (b'VA', b'Holy See (Vatican City State)'), (b'HN', b'Honduras'), (b'HK', b'Hong Kong'), (b'HU', b'Hungary'), (b'IS', b'Iceland'), (b'IN', b'India'), (b'ID', b'Indonesia'), (b'IR', b'Iran, Islamic Republic of'), (b'IQ', b'Iraq'), (b'IE', b'Ireland'), (b'IM', b'Isle of Man'), (b'IL', b'Israel'), (b'IT', b'Italy'), (b'JM', b'Jamaica'), (b'JP', b'Japan'), (b'JE', b'Jersey'), (b'JO', b'Jordan'), (b'KZ', b'Kazakhstan'), (b'KE', b'Kenya'), (b'KI', b'Kiribati'), (b'KP', b"Korea, Democratic People's Republic of"), (b'KR', b'Korea, Republic of'), (b'KW', b'Kuwait'), (b'KG', b'Kyrgyzstan'), (b'LA', b"Lao People's Democratic Republic"), (b'LV', b'Latvia'), (b'LB', b'Lebanon'), (b'LS', b'Lesotho'), (b'LR', b'Liberia'), (b'LY', b'Libya'), (b'LI', b'Liechtenstein'), (b'LT', b'Lithuania'), (b'LU', b'Luxembourg'), (b'MO', b'Macao'), (b'MK', b'Macedonia, The Former Yugoslav Republic of'), (b'MG', b'Madagascar'), (b'MW', b'Malawi'), (b'MY', b'Malaysia'), (b'MV', b'Maldives'), (b'ML', b'Mali'), (b'MT', b'Malta'), (b'MH', b'Marshall Islands'), (b'MQ', b'Martinique'), (b'MR', b'Mauritania'), (b'MU', b'Mauritius'), (b'YT', b'Mayotte'), (b'MX', b'Mexico'), (b'FM', b'Micronesia, Federated States of'), (b'MD', b'Moldova, Republic of'), (b'MC', b'Monaco'), (b'MN', b'Mongolia'), (b'ME', b'Montenegro'), (b'MS', b'Montserrat'), (b'MA', b'Morocco'), (b'MZ', b'Mozambique'), (b'MM', b'Myanmar'), (b'NA', b'Namibia'), (b'NR', b'Nauru'), (b'NP', b'Nepal'), (b'NL', b'Netherlands'), (b'NC', b'New Caledonia'), (b'NZ', b'New Zealand'), (b'NI', b'Nicaragua'), (b'NE', b'Niger'), (b'NG', b'Nigeria'), (b'NU', b'Niue'), (b'NF', b'Norfolk Island'), (b'MP', b'Northern Mariana Islands'), (b'NO', b'Norway'), (b'OM', b'Oman'), (b'PK', b'Pakistan'), (b'PW', b'Palau'), (b'PS', b'Palestine, State of'), (b'PA', b'Panama'), (b'PG', b'Papua New Guinea'), (b'PY', b'Paraguay'), (b'PE', b'Peru'), (b'PH', b'Philippines'), (b'PN', b'Pitcairn'), (b'PL', b'Poland'), (b'PT', b'Portugal'), (b'PR', b'Puerto Rico'), (b'QA', b'Qatar'), (b'RE', b'R\xc3\xa9union'), (b'RO', b'Romania'), (b'RU', b'Russian Federation'), (b'RW', b'Rwanda'), (b'BL', b'Saint Barth\xc3\xa9lemy'), (b'SH', b'Saint Helena, Ascension and Tristan da Cunha'), (b'KN', b'Saint Kitts and Nevis'), (b'LC', b'Saint Lucia'), (b'MF', b'Saint Martin (French part)'), (b'PM', b'Saint Pierre and Miquelon'), (b'VC', b'Saint Vincent and the Grenadines'), (b'WS', b'Samoa'), (b'SM', b'San Marino'), (b'ST', b'Sao Tome and Principe'), (b'SA', b'Saudi Arabia'), (b'SN', b'Senegal'), (b'RS', b'Serbia'), (b'SC', b'Seychelles'), (b'SL', b'Sierra Leone'), (b'SG', b'Singapore'), (b'SX', b'Sint Maarten (Dutch part)'), (b'SK', b'Slovakia'), (b'SI', b'Slovenia'), (b'SB', b'Solomon Islands'), (b'SO', b'Somalia'), (b'ZA', b'South Africa'), (b'GS', b'South Georgia and the South Sandwich Islands'), (b'SS', b'South Sudan'), (b'ES', b'Spain'), (b'LK', b'Sri Lanka'), (b'SD', b'Sudan'), (b'SR', b'Suriname'), (b'SJ', b'Svalbard and Jan Mayen'), (b'SZ', b'Swaziland'), (b'SE', b'Sweden'), (b'CH', b'Switzerland'), (b'SY', b'Syrian Arab Republic'), (b'TW', b'Taiwan, Province of China'), (b'TJ', b'Tajikistan'), (b'TZ', b'Tanzania, United Republic of'), (b'TH', b'Thailand'), (b'TL', b'Timor-Leste'), (b'TG', b'Togo'), (b'TK', b'Tokelau'), (b'TO', b'Tonga'), (b'TT', b'Trinidad and Tobago'), (b'TN', b'Tunisia'), (b'TR', b'Turkey'), (b'TM', b'Turkmenistan'), (b'TC', b'Turks and Caicos Islands'), (b'TV', b'Tuvalu'), (b'UG', b'Uganda'), (b'UA', b'Ukraine'), (b'AE', b'United Arab Emirates'), (b'GB', b'United Kingdom'), (b'US', b'United States'), (b'UM', b'United States Minor Outlying Islands'), (b'UY', b'Uruguay'), (b'UZ', b'Uzbekistan'), (b'VU', b'Vanuatu'), (b'VE', b'Venezuela, Bolivarian Republic of'), (b'VN', b'Viet Nam'), (b'VG', b'Virgin Islands, British'), (b'VI', b'Virgin Islands, U.S.'), (b'WF', b'Wallis and Futuna'), (b'EH', b'Western Sahara'), (b'YE', b'Yemen'), (b'ZM', b'Zambia'), (b'ZW', b'Zimbabwe')])),
                ('email', models.CharField(max_length=256, verbose_name='E-mail address')),
                ('website', models.CharField(max_length=256, null=True, verbose_name='Website', blank=True)),
                ('phone', models.CharField(max_length=30, null=True, verbose_name='Phone number', blank=True)),
                ('vat_no', models.CharField(max_length=30, verbose_name='VAT exemption number')),
                ('created_by', models.ForeignKey(related_name=b'pos_billcompany_created_by', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(related_name=b'pos_billcompany_updated_by', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='bill',
            name='issuer',
            field=models.ForeignKey(default=-1, to='pos.BillCompany'),
            preserve_default=False,
        ),
    ]
