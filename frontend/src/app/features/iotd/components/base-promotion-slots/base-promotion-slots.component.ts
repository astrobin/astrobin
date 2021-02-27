import { Component, EventEmitter, HostBinding, Input, OnInit, Output, QueryList, ViewChildren } from "@angular/core";
import { State } from "@app/store/state";
import { SubmissionInterface, VoteInterface } from "@features/iotd/services/iotd-api.service";
import { PromotionImageInterface } from "@features/iotd/store/iotd.reducer";
import { Store } from "@ngrx/store";
import { BaseComponentDirective } from "@shared/components/base-component.directive";
import { ImageComponent } from "@shared/components/misc/image/image.component";
import { ImageAlias } from "@shared/enums/image-alias.enum";
import { Observable } from "rxjs";
import { take, takeUntil } from "rxjs/operators";

interface Slot {
  id: number;
  promotion: SubmissionInterface | VoteInterface | null;
}

@Component({
  selector: "astrobin-base-promotion-slots",
  template: ""
})
export abstract class BasePromotionSlotsComponent extends BaseComponentDirective implements OnInit {
  ImageAlias = ImageAlias;

  abstract promotions$: Observable<SubmissionInterface[] | VoteInterface[]>;
  abstract slotsCount$: Observable<number>;
  slots: Slot[] = [];

  @Input()
  availableEntries: PromotionImageInterface[] = [];

  @Output()
  slotClick = new EventEmitter();

  @ViewChildren("image")
  _images = new QueryList<ImageComponent>();

  protected constructor(public readonly store$: Store<State>) {
    super();
  }

  @HostBinding("class.is-empty")
  public get isEmpty(): boolean {
    return this.slots.filter(slot => !!slot.promotion).length === 0;
  }

  ngOnInit() {
    this.slotsCount$.pipe(take(1)).subscribe(count => {
      for (let i = 0; i < count; ++i) {
        this.slots.push({
          id: i,
          promotion: null
        });
      }
    });

    this.promotions$.pipe(takeUntil(this.destroyed$)).subscribe(submissions => {
      this.slots.forEach(slot => (slot.promotion = null));
      submissions.forEach((promotion, i) => {
        this.slots[i].promotion = promotion;
      });

      this._images.forEach(image => image.refresh());
    });
  }

  slotClicked(imageId: number): void {
    if (this.clickableSlot(imageId)) {
      this.slotClick.emit(imageId);
    }
  }

  clickableSlot(imageId: number): boolean {
    return this.availableEntries.map(submission => submission.pk).indexOf(imageId) !== -1;
  }
}
