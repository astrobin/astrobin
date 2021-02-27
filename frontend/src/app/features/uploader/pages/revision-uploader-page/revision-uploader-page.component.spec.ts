import { ActivatedRoute } from "@angular/router";
import { AppModule } from "@app/app.module";
import { RevisionUploaderPageComponent } from "@features/uploader/pages/revision-uploader-page/revision-uploader-page.component";
import { UploaderModule } from "@features/uploader/uploader.module";
import { ImageGenerator } from "@shared/generators/image.generator";
import { MockBuilder, MockRender } from "ng-mocks";

describe("RevisionUploader.PageComponent", () => {
  beforeEach(() =>
    MockBuilder(RevisionUploaderPageComponent, UploaderModule)
      .mock(AppModule)
      .provide([
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              data: {
                image: ImageGenerator.image()
              }
            }
          }
        }
      ])
  );

  it("should create", () => {
    const fixture = MockRender(RevisionUploaderPageComponent);
    expect(fixture.point.componentInstance).toBeTruthy();
  });
});
