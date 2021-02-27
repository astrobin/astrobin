import {
  AfterViewChecked,
  ChangeDetectorRef,
  Component,
  ElementRef,
  HostBinding,
  Input,
  OnChanges,
  OnInit,
  SimpleChanges,
  ViewChild
} from "@angular/core";
import { DomSanitizer, SafeUrl } from "@angular/platform-browser";
import { LoadImage } from "@app/store/actions/image.actions";
import { LoadThumbnail } from "@app/store/actions/thumbnail.actions";
import { selectImage } from "@app/store/selectors/app/image.selectors";
import { selectThumbnail } from "@app/store/selectors/app/thumbnail.selectors";
import { State } from "@app/store/state";
import { Store } from "@ngrx/store";
import { BaseComponentDirective } from "@shared/components/base-component.directive";
import { ImageAlias } from "@shared/enums/image-alias.enum";
import { ImageInterface } from "@shared/interfaces/image.interface";
import { ImageApiService } from "@shared/services/api/classic/images/image/image-api.service";
import { ThumbnailGroupApiService } from "@shared/services/api/classic/images/thumbnail-group/thumbnail-group-api.service";
import { ImageService } from "@shared/services/image/image.service";
import { UtilsService } from "@shared/services/utils/utils.service";
import { WindowRefService } from "@shared/services/window-ref.service";
import { BehaviorSubject, fromEvent, Observable } from "rxjs";
import { debounceTime, distinctUntilChanged, filter, map, switchMap, takeUntil, tap } from "rxjs/operators";

@Component({
  selector: "astrobin-image",
  templateUrl: "./image.component.html",
  styleUrls: ["./image.component.scss"]
})
export class ImageComponent extends BaseComponentDirective implements OnInit, OnChanges, AfterViewChecked {
  image$: Observable<ImageInterface>;
  thumbnailUrl$: Observable<SafeUrl>;

  @Input()
  @HostBinding("attr.data-id")
  id: number;

  @Input()
  revision = "final";

  @Input()
  alias: ImageAlias;

  @Input()
  alwaysLoad = false;

  @HostBinding("class.loading")
  loading = false;

  loadingProgress$: Observable<number>;

  @ViewChild("loadingIndicator", { read: ElementRef })
  private _loadingIndicator: ElementRef;

  private _loadingProgressSubject = new BehaviorSubject<number>(0);

  private _loaded = false;

  constructor(
    public readonly store$: Store<State>,
    public readonly imageApiService: ImageApiService,
    public readonly thumbnailGroupApiService: ThumbnailGroupApiService,
    public readonly imageService: ImageService,
    public readonly elementRef: ElementRef,
    public readonly changeDetector: ChangeDetectorRef,
    public readonly utilsService: UtilsService,
    public readonly windowRefService: WindowRefService,
    public readonly domSanitizer: DomSanitizer
  ) {
    super();

    this.loadingProgress$ = this._loadingProgressSubject.asObservable();
  }

  ngOnInit(): void {
    if (this.id === null) {
      throw new Error("Attribute 'id' is required");
    }

    if (this.alias === null) {
      throw new Error("Attribute 'alias' is required");
    }

    fromEvent(this.windowRefService.nativeWindow, "scroll")
      .pipe(takeUntil(this.destroyed$), debounceTime(50), distinctUntilChanged())
      .subscribe(() => this._load());
  }

  ngOnChanges(changes: SimpleChanges): void {
    setTimeout(() => {
      this._loaded = false;
      this._load();
    }, 1);
  }

  ngAfterViewChecked() {
    this.changeDetector.detectChanges();
  }

  refresh(): void {
    this._loaded = false;
    this.loading = true;
    this._loadImage();
  }

  private _load(): void {
    if (
      !this._loaded &&
      this._loadingIndicator &&
      (this.utilsService.isInViewport(this._loadingIndicator.nativeElement) || this.alwaysLoad)
    ) {
      this.loading = true;
      this._loadImage();
    }
  }

  private _loadImage() {
    this.store$.dispatch(new LoadImage(this.id));

    this.image$ = this.store$.select(selectImage, this.id).pipe(
      filter(image => !!image),
      tap(() => {
        this._loadThumbnail();
      })
    );
  }

  private _loadThumbnail() {
    this.store$.dispatch(new LoadThumbnail({ id: this.id, revision: this.revision, alias: this.alias }));

    this.thumbnailUrl$ = this.store$
      .select(selectThumbnail, {
        id: this.id,
        revision: this.revision,
        alias: this.alias
      })
      .pipe(
        filter(thumbnail => !!thumbnail),
        switchMap(thumbnail =>
          this.imageService.loadImageFile(thumbnail.url, (progress: number) => {
            this._loadingProgressSubject.next(progress);
          })
        ),
        map(url => this.domSanitizer.bypassSecurityTrustUrl(url)),
        tap(() => {
          this.loading = false;
          this._loaded = true;
        })
      );
  }
}
