from ...Core.Node.Core import ConditionalNode, NodeOutput, PoolType
import asyncio
import structlog
import random

logger = structlog.get_logger(__name__)

class IfCondition(ConditionalNode):
    @classmethod
    def identifier(cls) -> str:
        return "if-condition"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.ASYNC

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        
        # Get condition from form
        form_data = self.node_config.data.form or {}
        expression = form_data.get("condition_expression", "")
        
        if not expression:
            logger.warning("No condition expression provided, defaulting to False", node_id=self.node_config.id)
            self.set_output(False)
            return node_data

        try:
            # Evaluate expression with 'data' in context
            # Using eval with restricted scope for basic safety
            context = {"data": node_data.data}
            result = eval(expression, {"__builtins__": {}}, context)
            
            # Ensure boolean result
            is_true = bool(result)
            
            logger.info(
                "Evaluated Condition", 
                expression=expression, 
                result=is_true, 
                node_id=self.node_config.id
            )
            
            self.set_output(is_true)
            
        except Exception as e:
            logger.error("Condition evaluation failed", error=str(e), expression=expression)
            raise ValueError(f"Failed to evaluate condition '{expression}': {str(e)}")
        
        return NodeOutput(
            id=self.node_config.id,
            data=node_data.data,
            metadata=node_data.metadata
        )
