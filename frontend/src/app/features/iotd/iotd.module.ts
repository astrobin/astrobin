import { NgModule } from "@angular/core";
import { RouterModule } from "@angular/router";
import { ReviewEntryComponent } from "@features/iotd/components/review-entry/review-entry.component";
import { ReviewSlotsComponent } from "@features/iotd/components/review-slots/review-slots.component";
import { SubmissionEntryComponent } from "@features/iotd/components/submission-entry/submission-entry.component";
import { SubmissionSlotsComponent } from "@features/iotd/components/submission-slots/submission-slots.component";
import { routes } from "@features/iotd/iotd.routing";
import { ReviewQueueComponent } from "@features/iotd/pages/review-queue/review-queue.component";
import { IotdApiService } from "@features/iotd/services/iotd-api.service";
import { EffectsModule } from "@ngrx/effects";
import { StoreModule } from "@ngrx/store";
import { SharedModule } from "@shared/shared.module";
import { ConfirmDismissModalComponent } from "./components/confirm-dismiss-modal/confirm-dismiss-modal.component";
import { SubmissionQueueComponent } from "./pages/submission-queue/submission-queue.component";
import { IotdEffects } from "./store/iotd.effects";
import * as fromIotd from "./store/iotd.reducer";

@NgModule({
  declarations: [
    SubmissionEntryComponent,
    SubmissionSlotsComponent,
    ReviewEntryComponent,
    ReviewSlotsComponent,
    ReviewQueueComponent,
    SubmissionQueueComponent,
    ConfirmDismissModalComponent
  ],
  imports: [
    RouterModule.forChild(routes),
    SharedModule,
    StoreModule.forFeature(fromIotd.iotdFeatureKey, fromIotd.reducer),
    EffectsModule.forFeature([IotdEffects])
  ],
  providers: [IotdApiService],
  exports: [RouterModule, SharedModule, StoreModule, EffectsModule]
})
export class IotdModule {}
