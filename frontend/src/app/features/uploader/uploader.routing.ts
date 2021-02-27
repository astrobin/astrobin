import { Routes } from "@angular/router";
import { UploaderPageComponent } from "@features/uploader/pages/uploader-page/uploader-page.component";
import { UploaderGuardService } from "@features/uploader/services/guards/uploader-guard.service";
import { ImageResolver } from "@shared/resolvers/image.resolver";
import { AuthGuardService } from "@shared/services/guards/auth-guard.service";
import { ImageOwnerGuardService } from "@shared/services/guards/image-owner-guard.service";
import { RevisionUploaderPageComponent } from "./pages/revision-uploader-page/revision-uploader-page.component";
import { UncompressedSourceUploaderPageComponent } from "./pages/uncompressed-source-uploader-page/uncompressed-source-uploader-page.component";

export const routes: Routes = [
  {
    path: "",
    canActivate: [AuthGuardService],
    // Using children routes to make the AuthGuardService have priority over the UltimateSubscriptionGuardService.
    children: [
      {
        path: "",
        component: UploaderPageComponent
      },
      {
        path: "revision/:imageId",
        canActivate: [UploaderGuardService, ImageOwnerGuardService],
        component: RevisionUploaderPageComponent,
        resolve: {
          image: ImageResolver
        }
      },
      {
        path: "uncompressed-source/:imageId",
        canActivate: [UploaderGuardService, ImageOwnerGuardService],
        component: UncompressedSourceUploaderPageComponent,
        resolve: {
          image: ImageResolver
        }
      }
    ]
  }
];
