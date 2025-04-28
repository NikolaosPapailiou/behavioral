# Behavioral

Reactive, modular and reusable behaviors for AI agents.

## Agent manifesto

### Modularity

Agents should be modular, allowing their components to be developed, tested, and reused independently. As systems grow in complexity, it becomes increasingly valuable to work with individual parts rather than the entire system at once.

### Reactivity

Agents must be capable of quickly and efficiently responding to changes in their environment—not just reacting to user input, but adapting proactively to evolving conditions.

### Reusability

Agents should not require building from scratch for every new project. Instead, we need robust agentic libraries that allow tools and behaviors to be easily reused across different applications.

## Why Behavior Trees?

<p align="center">
    <img
      src="./assets/fsms.jpg"
    />
</p>

### Modularity

Behavior Trees (BTs) naturally support modularity. Each node, whether it's a single action or a complex behavior, acts as a self-contained unit. This allows behaviors to be developed, tested, and maintained independently, making it easier to manage complexity as systems grow.

### Reactivity

BTs are inherently reactive. Rather than following a fixed sequence of actions, they continuously "tick" through the tree, evaluating conditions and selecting or interrupting actions based on the current state of the environment. This process is hierarchical and priority-driven, allowing high-level behaviors to seamlessly take control from lower-level behaviors at any point during execution.

### Reusability

BTs promote high reusability of code and behaviors. Well-defined nodes and subtrees can be reused across different agents or tasks, reducing duplication and accelerating development. Libraries of behavior modules can be built up over time, leading to faster iteration and more robust systems.

### Hierarchical Structure

BTs organize behaviors hierarchically, from high-level goals down to fine-grained actions. This mirrors human planning and decision-making, making the structure easy to understand, design, and debug. Each layer of the tree abstracts details from the layer below, leading to cleaner and more maintainable systems.

### Human Readable

The tree-based format of BTs results in a clear and intuitive visual and logical structure. Developers can easily trace how an agent will behave in different scenarios, making development, debugging, and collaboration more efficient, even as systems scale up.


## Test it out!

You can run our demo locally by following the instructions [here](./demo/README.md)

<p align="center">
    <img
      src="./assets/demo.png"
    />
</p>

## Installation

You can install the package directly from the source:

```bash
pip install .
```
## Code examples

See our code examples [here](./demo/examples/)

## Requirements

See requirements.txt for full dependencies

## Development

To set up the development environment:

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## License

This project is licensed under the MIT License. 