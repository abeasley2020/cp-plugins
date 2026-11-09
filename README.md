# cp-plugins

Claude plugins from Course Production at Purdue University Online, shared with the instructional design team.

## Plugins

| Plugin | What it does |
|---|---|
| [course-production-agents](course-production-agents/) | Turns a folder of faculty content into a course map, a media plan, and one Brightspace package (SCORM 1.2 and HTML) per module or week, with optional infographics that each carry a full text description. Every page is Purdue branded and checked against WCAG 2.2 AA. |

Each plugin folder has its own README covering setup, what it runs, and how to use it.

## Example

[`examples/fspg-101`](examples/fspg-101) is a complete run of course-production-agents on a fictional four-week course, FSPG 101 (Food Safety for Small-Scale Produce Growers). `faculty-content/` is the input folder and `output/` is everything the plugin produced: course map, media plan, topic files, review pages, packages and the accessibility report. No real faculty material is included.

## Support

Report problems or ask questions in [GitHub Issues](https://github.com/abeasley2020/cp-plugins/issues).

## License

MIT. See [LICENSE](LICENSE).
