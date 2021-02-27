import { Component, OnInit, TemplateRef, ViewChild } from "@angular/core";
import { FormGroup } from "@angular/forms";
import { ActivatedRoute } from "@angular/router";
import { SetBreadcrumb } from "@app/store/actions/breadcrumb.actions";
import { State } from "@app/store/state";
import { selectCurrentUser } from "@features/account/store/auth.selectors";
import { Store } from "@ngrx/store";
import { FormlyFieldConfig } from "@ngx-formly/core";
import { TranslateService } from "@ngx-translate/core";
import { BaseComponentDirective } from "@shared/components/base-component.directive";
import { ImageAlias } from "@shared/enums/image-alias.enum";
import {
  AcquisitionType,
  DataSource,
  ImageInterface,
  MouseHoverImageOptions,
  RemoteSource,
  SolarSystemSubjectType,
  SubjectType
} from "@shared/interfaces/image.interface";
import { RemoteSourceAffiliateInterface } from "@shared/interfaces/remote-source-affiliate.interface";
import { GroupApiService } from "@shared/services/api/classic/groups/group-api.service";
import { RemoteSourceAffiliateApiService } from "@shared/services/api/classic/remote-source-affiliation/remote-source-affiliate-api.service";
import { ClassicRoutesService } from "@shared/services/classic-routes.service";
import { TitleService } from "@shared/services/title/title.service";
import { map, switchMap } from "rxjs/operators";

@Component({
  selector: "astrobin-image-edit-page",
  templateUrl: "./image-edit-page.component.html",
  styleUrls: ["./image-edit-page.component.scss"]
})
export class ImageEditPageComponent extends BaseComponentDirective implements OnInit {
  ImageAlias = ImageAlias;
  image: ImageInterface;
  model: Partial<ImageInterface>;
  form = new FormGroup({});
  fields: FormlyFieldConfig[];
  remoteSourceAffiliates: RemoteSourceAffiliateInterface[];

  @ViewChild("remoteSourceLabelTemplate")
  remoteSourceLabelTemplate: TemplateRef<any>;

  @ViewChild("remoteSourceOptionTemplate")
  remoteSourceOptionTemplate: TemplateRef<any>;

  constructor(
    public readonly store$: Store<State>,
    public readonly route: ActivatedRoute,
    public readonly translate: TranslateService,
    public readonly classicRoutesService: ClassicRoutesService,
    public readonly titleService: TitleService,
    public readonly remoteSourceAffiliateApiService: RemoteSourceAffiliateApiService,
    public readonly groupApiService: GroupApiService
  ) {
    super();
  }

  ngOnInit(): void {
    this.image = this.route.snapshot.data.image;
    this.model = { ...this.image };
    this.titleService.setTitle("Edit image");

    this._initBreadcrumb();

    this.remoteSourceAffiliateApiService.getAll().subscribe(remoteSourceAffiliates => {
      this.remoteSourceAffiliates = remoteSourceAffiliates;
      this._initFields();
    });
  }

  public isSponsor(code: string): boolean {
    return (
      this.remoteSourceAffiliates.filter(affiliate => {
        const now = new Date();
        return (
          affiliate.code === code &&
          new Date(affiliate.affiliationStart) <= now &&
          new Date(affiliate.affiliationExpiration) > now
        );
      }).length > 0
    );
  }

  onSubmit(): void {}

  private _getTitleField(): any {
    return {
      key: "title",
      type: "input",
      templateOptions: {
        label: this.translate.instant("Title"),
        required: true
      }
    };
  }

  private _getDescriptionField(): any {
    return {
      key: "description",
      type: "textarea",
      templateOptions: {
        label: this.translate.instant("Description"),
        description: this.translate.instant("HTML tags are allowed."),
        required: false,
        rows: 10
      }
    };
  }

  private _getLinkField(): any {
    return {
      key: "link",
      type: "input",
      templateOptions: {
        label: this.translate.instant("Link"),
        description: this.translate.instant(
          "If you're hosting a copy of this image on your website, put the address here."
        ),
        placeholder: "https://www.example.com/my-page.html",
        required: false
      }
    };
  }

  private _getLinkToFitsField(): any {
    return {
      key: "linkToFits",
      type: "input",
      templateOptions: {
        label: this.translate.instant("Link to TIFF/FITS"),
        description: this.translate.instant(
          "If you want to share the TIFF or FITS file of your image, put a link to the file here. " +
            "Unfortunately, AstroBin cannot offer to store these files at the moment, so you will have to " +
            "host them on your personal space."
        ),
        placeholder: "https://www.example.com/my-page.html",
        required: false
      }
    };
  }

  private _getAcquisitionTypeField(): any {
    return {
      key: "acquisitionType",
      type: "ng-select",
      templateOptions: {
        required: true,
        label: this.translate.instant("Acquisition type"),
        options: [
          {
            value: AcquisitionType.REGULAR,
            label: this.translate.instant("Regular (e.g. medium/long exposure with a CCD or DSLR)")
          },
          {
            value: AcquisitionType.EAA,
            label: this.translate.instant("Electronically-Assisted Astronomy (EAA, e.g. based on a live video feed)")
          },
          {
            value: AcquisitionType.LUCKY,
            label: this.translate.instant("Lucky imaging")
          },
          {
            value: AcquisitionType.DRAWING,
            label: this.translate.instant("Drawing/Sketch")
          },
          {
            value: AcquisitionType.OTHER,
            label: this.translate.instant("Other/Unknown")
          }
        ]
      }
    };
  }

  private _getSubjectTypeField(): any {
    return {
      key: "subjectType",
      type: "ng-select",
      templateOptions: {
        required: true,
        label: this.translate.instant("Subject type"),
        options: [
          { value: SubjectType.DEEP_SKY, label: this.translate.instant("Deep sky object or field") },
          { value: SubjectType.SOLAR_SYSTEM, label: this.translate.instant("Solar system body or event") },
          { value: SubjectType.WIDE_FIELD, label: this.translate.instant("Extremely wide field") },
          { value: SubjectType.STAR_TRAILS, label: this.translate.instant("Star trails") },
          { value: SubjectType.NORTHERN_LIGHTS, label: this.translate.instant("Northern lights") },
          { value: SubjectType.GEAR, label: this.translate.instant("Gear") },
          { value: SubjectType.OTHER, label: this.translate.instant("Other") }
        ]
      },
      hooks: {
        onInit: (field: FormlyFieldConfig) => {
          field.formControl.valueChanges.subscribe(value => {
            if (value !== SubjectType.SOLAR_SYSTEM) {
              this.model.solarSystemMainSubject = null;
            }
          });
        }
      }
    };
  }

  private _getSolarSystemMainSubjectField(): any {
    return {
      key: "solarSystemMainSubject",
      type: "ng-select",
      hideExpression: () => this.model.subjectType !== SubjectType.SOLAR_SYSTEM,
      expressionProperties: {
        "templateOptions.required": "model.subjectType === 'SOLAR_SYSTEM'"
      },
      templateOptions: {
        label: this.translate.instant("Main solar system subject"),
        options: [
          { value: SolarSystemSubjectType.SUN, label: this.translate.instant("Sun") },
          { value: SolarSystemSubjectType.MOON, label: this.translate.instant("Earth's Moon") },
          { value: SolarSystemSubjectType.MERCURY, label: this.translate.instant("Mercury") },
          { value: SolarSystemSubjectType.VENUS, label: this.translate.instant("Venus") },
          { value: SolarSystemSubjectType.MARS, label: this.translate.instant("Mars") },
          { value: SolarSystemSubjectType.JUPITER, label: this.translate.instant("Jupiter") },
          { value: SolarSystemSubjectType.SATURN, label: this.translate.instant("Saturn") },
          { value: SolarSystemSubjectType.URANUS, label: this.translate.instant("Uranus") },
          { value: SolarSystemSubjectType.NEPTUNE, label: this.translate.instant("Neptune") },
          { value: SolarSystemSubjectType.MINOR_PLANET, label: this.translate.instant("Minor planet") },
          { value: SolarSystemSubjectType.COMET, label: this.translate.instant("Comet") },
          { value: SolarSystemSubjectType.OCCULTATION, label: this.translate.instant("Occultation") },
          { value: SolarSystemSubjectType.CONJUNCTION, label: this.translate.instant("Conjunction") },
          {
            value: SolarSystemSubjectType.PARTIAL_LUNAR_ECLIPSE,
            label: this.translate.instant("Partial lunar eclipse")
          },
          {
            value: SolarSystemSubjectType.TOTAL_LUNAR_ECLIPSE,
            label: this.translate.instant("Total lunar eclipse")
          },
          {
            value: SolarSystemSubjectType.PARTIAL_SOLAR_ECLIPSE,
            label: this.translate.instant("Partial solar eclipse")
          },
          {
            value: SolarSystemSubjectType.ANULAR_SOLAR_ECLIPSE,
            label: this.translate.instant("Anular solar eclipse")
          },
          {
            value: SolarSystemSubjectType.TOTAL_SOLAR_ECLIPSE,
            label: this.translate.instant("Total solar eclipse")
          },
          { value: SolarSystemSubjectType.OTHER, label: this.translate.instant("Other") }
        ]
      }
    };
  }

  private _getDataSourceField(): any {
    return {
      key: "dataSource",
      type: "ng-select",
      templateOptions: {
        required: true,
        label: this.translate.instant("Data source"),
        description: this.translate.instant("Where does the data for this image come from?"),
        options: [
          {
            value: DataSource.BACKYARD,
            label: this.translate.instant("Backyard"),
            group: this.translate.instant("Self acquired")
          },
          {
            value: DataSource.TRAVELLER,
            label: this.translate.instant("Traveller"),
            group: this.translate.instant("Self acquired")
          },
          {
            value: DataSource.OWN_REMOTE,
            label: this.translate.instant("Own remote observatory"),
            group: this.translate.instant("Self acquired")
          },
          {
            value: DataSource.AMATEUR_HOSTING,
            label: this.translate.instant("Amateur hosting facility"),
            group: this.translate.instant("Downloaded")
          },
          {
            value: DataSource.PUBLIC_AMATEUR_DATA,
            label: this.translate.instant("Public amateur data"),
            group: this.translate.instant("Downloaded")
          },
          {
            value: DataSource.PRO_DATA,
            label: this.translate.instant("Professional, scientific grade data"),
            group: this.translate.instant("Downloaded")
          },
          {
            value: DataSource.MIX,
            label: this.translate.instant("Mix of multiple sources"),
            group: this.translate.instant("Other")
          },
          {
            value: DataSource.OTHER,
            label: this.translate.instant("None of the above"),
            group: this.translate.instant("Other")
          },
          {
            value: DataSource.UNKNOWN,
            label: this.translate.instant("Unknown"),
            group: this.translate.instant("Other")
          }
        ]
      },
      hooks: {
        onInit: (field: FormlyFieldConfig) => {
          field.formControl.valueChanges.subscribe(value => {
            if ([DataSource.OWN_REMOTE, DataSource.AMATEUR_HOSTING].indexOf(value) === -1) {
              this.model.remoteSource = null;
            }
          });
        }
      }
    };
  }

  private _getRemoteSourceField(): any {
    return {
      key: "remoteSource",
      type: "ng-select",
      hideExpression: () => [DataSource.OWN_REMOTE, DataSource.AMATEUR_HOSTING].indexOf(this.model.dataSource) === -1,
      expressionProperties: {
        "templateOptions.required": "model.dataSource === 'OWN_REMOTE' || model.dataSource === 'AMATEUR_HOSTING'"
      },
      templateOptions: {
        label: this.translate.instant("Remote data source"),
        description: this.translate.instant(
          "Which remote hosting facility did you use to acquire data for this image?"
        ),
        labelTemplate: this.remoteSourceLabelTemplate,
        optionTemplate: this.remoteSourceOptionTemplate,
        options: [
          ...Array.from(Object.keys(RemoteSource)).map(key => ({
            value: key,
            label: RemoteSource[key],
            group: this.translate.instant("Commercial facilities")
          })),
          {
            value: "OWN",
            label: this.translate.instant("Non-commercial independent facility"),
            group: this.translate.instant("Other")
          },
          {
            value: "OTHER",
            label: this.translate.instant("None of the above"),
            group: this.translate.instant("Other")
          }
        ]
      }
    };
  }

  private _getGroupsField(): any {
    return {
      key: "partOfGroupSet",
      type: "ng-select",
      templateOptions: {
        multiple: true,
        required: false,
        label: this.translate.instant("Groups"),
        description: this.translate.instant("Submit this image to the selected groups."),
        options: this.store$.select(selectCurrentUser).pipe(
          switchMap(user =>
            this.groupApiService.getAll(user.id).pipe(
              map(groups =>
                groups.map(group => ({
                  value: group.id,
                  label: group.name
                }))
              )
            )
          )
        )
      }
    };
  }

  private _getKeyValueTagsField(): any {
    return {
      key: "keyValueTags",
      type: "textarea",
      templateOptions: {
        rows: 5,
        required: false,
        label: this.translate.instant("Key/value tags"),
        description: this.translate.instant(
          "Provide a list of unique key/value pairs to tag this image with. " +
            "Use the '=' symbol between key and value, and provide one pair per line. These tags can be used to sort " +
            "images by arbitrary properties."
        )
      }
    };
  }

  private _getMouseHoverImageField(): any {
    return {
      key: "mouseHoverImage",
      type: "ng-select",
      templateOptions: {
        required: true,
        label: this.translate.instant("Mouse hover image"),
        description: this.translate.instant(
          "Choose what will be displayed when somebody hovers the mouse over this image. Please note: only " +
            "revisions with the same width and height of your original image can be considered."
        ),
        options: [
          {
            value: MouseHoverImageOptions.NOTHING,
            label: this.translate.instant("Nothing")
          },
          {
            value: MouseHoverImageOptions.SOLUTION,
            label: this.translate.instant("Plate-solution annotations (if available)")
          },
          {
            value: MouseHoverImageOptions.INVERTED,
            label: this.translate.instant("Inverted monochrome")
          }
        ]
      }
    };
  }

  private _getAllowCommentsField(): any {
    return {
      key: "allowComments",
      type: "checkbox",
      templateOptions: {
        label: this.translate.instant("Allow comments")
      }
    };
  }

  private _initFields(): void {
    this.fields = [
      {
        type: "image-edit-stepper",
        templateOptions: {
          image: this.image
        },
        fieldGroup: [
          {
            templateOptions: { label: this.translate.instant("Basic information") },
            fieldGroup: [
              this._getTitleField(),
              this._getDescriptionField(),
              this._getLinkField(),
              this._getLinkToFitsField()
            ]
          },
          {
            templateOptions: { label: this.translate.instant("Content") },
            fieldGroup: [
              this._getAcquisitionTypeField(),
              this._getSubjectTypeField(),
              this._getSolarSystemMainSubjectField(),
              this._getDataSourceField(),
              this._getRemoteSourceField(),
              this._getGroupsField()
            ]
          },
          {
            templateOptions: { label: this.translate.instant("Settings") },
            fieldGroup: [this._getKeyValueTagsField(), this._getMouseHoverImageField(), this._getAllowCommentsField()]
          }
        ]
      }
    ];
  }

  private _initBreadcrumb(): void {
    this.store$.dispatch(
      new SetBreadcrumb({
        breadcrumb: [
          {
            label: this.translate.instant("Image")
          },
          {
            label: this.image.title
          },
          {
            label: this.translate.instant("Edit")
          }
        ]
      })
    );
  }
}
