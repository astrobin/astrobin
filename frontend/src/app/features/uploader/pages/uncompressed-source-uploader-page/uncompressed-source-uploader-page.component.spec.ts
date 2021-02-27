import { ActivatedRoute } from "@angular/router";
import { AppModule } from "@app/app.module";
import { UncompressedSourceUploaderPageComponent } from "@features/uploader/pages/uncompressed-source-uploader-page/uncompressed-source-uploader-page.component";
import { UploaderModule } from "@features/uploader/uploader.module";
import { ImageGenerator } from "@shared/generators/image.generator";
import { MockBuilder, MockRender } from "ng-mocks";

describe("UncompressedSourceUploader.PageComponent", () => {
  let component: UncompressedSourceUploaderPageComponent;

  beforeEach(() =>
    MockBuilder(UncompressedSourceUploaderPageComponent, UploaderModule)
      .mock(AppModule)
      .provide({
        provide: ActivatedRoute,
        useValue: {
          snapshot: {
            data: {
              image: ImageGenerator.image()
            }
          }
        }
      })
  );

  beforeEach(() => {
    const fixture = MockRender(UncompressedSourceUploaderPageComponent);
    component = fixture.point.componentInstance;
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
